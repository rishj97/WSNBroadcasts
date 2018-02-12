/**
 * \file
 *         Naive Flooding
 * \author
 *         AESE Group
 */

#include "contiki.h"
#include "net/rime/rime.h"
#include "random.h"
#include "net/netstack.h"
#include "dev/leds.h"
#include "dev/serial-line.h"

#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <powertrace.h>
#define NO_OF_NODES 10
// power trace interval in seconds
#define POWERTRACE_INTERVAL 10

#define RADIO_OFF_INTERVAL 7

struct message{
  uint16_t flood_id;
  uint8_t node_count;
  uint8_t nodes[NO_OF_NODES];
  uint8_t hops;
};

struct message payload_send,payload_recv;
static struct broadcast_conn broadcast;
static struct ctimer message_sent;
static struct ctimer turn_mac_on;
static struct ctimer brdcast_send;
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

static void
send_brdcast(void *ptr){
  broadcast_send(&broadcast);
}
/*---------------------------------------------------------------------------*/
static void
broadcast_recv(struct broadcast_conn *c, const linkaddr_t *from)
{
  bool received = false;

  packetbuf_copyto(&payload_recv);

  printf("Broadcast recv from %d of %d with id %d\n", from->u8[0],payload_recv.nodes[0],payload_recv.flood_id);

  int i = 0;
  for(i = 0; i < payload_recv.node_count;i++){
    if(payload_recv.nodes[i] == linkaddr_node_addr.u8[0]){
      received = true;
      break;
    }
  }

  if(payload_recv.node_count > (NO_OF_NODES-1)){
      received = true;
  }

  payload_recv.hops += 1;

  if(!received || payload_recv.hops < 3){
    payload_recv.nodes[payload_recv.node_count]  = linkaddr_node_addr.u8[0];
    payload_recv.node_count = payload_recv.node_count + 1;

    packetbuf_copyfrom(&payload_recv,sizeof(payload_recv));
    ctimer_set(&brdcast_send, random_rand() % 5 * 0.001 * CLOCK_SECOND, send_brdcast, NULL);

    printf("Broadcast message sent\n");
    if(linkaddr_node_addr.u8[0] == 1){
      ctimer_reset(&message_sent);
    }
  } else {
    NETSTACK_MAC.off(0);
    ctimer_set(&turn_mac_on, CLOCK_SECOND * RADIO_OFF_INTERVAL, mac_on, NULL);
  }
}

static const struct broadcast_callbacks broadcast_call = {broadcast_recv};

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(main_process, ev, data)
{
  PROCESS_EXITHANDLER(broadcast_close(&broadcast);)
  char *buf;

  PROCESS_BEGIN();
  powertrace_start(CLOCK_SECOND * POWERTRACE_INTERVAL);
  broadcast_open(&broadcast, 129, &broadcast_call);
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
      payload_send.hops = 0;
      packetbuf_copyfrom(&payload_send, sizeof(payload_recv));
      NETSTACK_MAC.on();
      broadcast_send(&broadcast);
      printf("Broadcast message sent %d\n",atoi(buf));

      if(linkaddr_node_addr.u8[0] == 1){
        ctimer_restart(&message_sent);
      }

    }

  PROCESS_END();
}
/*---------------------------------------------------------------------------*/
