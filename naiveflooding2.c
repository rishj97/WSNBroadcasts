/**
 * \file
 *         Naive Flooding
 * \author
 *         AESE Group
 */

#include "contiki.h"
#include "net/rime/rime.h"
#include "random.h"
#include "mynetflood.h"
#include "net/netstack.h"
#include "dev/leds.h"
#include "dev/serial-line.h"

#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <powertrace.h>
#define NO_OF_NODES 30
// power trace interval in seconds
#define POWERTRACE_INTERVAL 10

#define RADIO_OFF_INTERVAL 7

struct message{
  uint16_t flood_id;
  uint8_t node_count;
  uint8_t nodes[NO_OF_NODES];
};

struct message payload_send,payload_recv;
static struct netflood_conn netflood;
static struct ctimer message_sent;
static struct ctimer turn_mac_on;
/*---------------------------------------------------------------------------*/
PROCESS(main_process, "Naive Flooding");
AUTOSTART_PROCESSES(&main_process);

/* callback function to request a message
 * if node 1 has not seen a message for 10 seconds
 */
static void
request_message(void *ptr){
  ctimer_restart(&message_sent);
  printf("Send me a message\n");
}

static void
mac_on(void *ptr){
  NETSTACK_MAC.on();
}
/*---------------------------------------------------------------------------*/
static void
netflood_recv(struct netflood_conn *c, const linkaddr_t *from, const linkaddr_t *originator, uint8_t seqno, uint8_t hops)
{
  bool received = false;

  packetbuf_copyto(&payload_recv);

  printf("Broadcast recv from %d of %d with id %d\n", from->u8[0],payload_recv.nodes[0],payload_recv.flood_id);
  NETSTACK_MAC.off(0);
  ctimer_set(&turn_mac_on, CLOCK_SECOND * RADIO_OFF_INTERVAL, mac_on, NULL);
}

static const struct netflood_callbacks netflood_call = {netflood_recv};

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(main_process, ev, data)
{
  PROCESS_EXITHANDLER(netflood_close(&netflood);)
  char *buf;

  PROCESS_BEGIN();
  powertrace_start(CLOCK_SECOND * POWERTRACE_INTERVAL);
  netflood_open(&netflood, 2, 129, &netflood_call);
  if(linkaddr_node_addr.u8[0] == 1){
    ctimer_set(&message_sent, CLOCK_SECOND * 10,request_message,NULL);
  }

  while(1) {
      /* Wait until javascript sends a counter value */
      PROCESS_WAIT_EVENT_UNTIL(ev == serial_line_event_message && data != NULL);
      buf = (char *)data;

      payload_send.flood_id = atoi(buf);
      payload_send.nodes[0] = linkaddr_node_addr.u8[0];
      payload_send.node_count = 1;
      packetbuf_copyfrom(&payload_send, sizeof(payload_recv));
      NETSTACK_MAC.on();
      netflood_send(&netflood, atoi(buf));
      printf("Broadcast message sent %d\n",atoi(buf));
      if(linkaddr_node_addr.u8[0] == 1){
        ctimer_restart(&message_sent);
      }
    }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
