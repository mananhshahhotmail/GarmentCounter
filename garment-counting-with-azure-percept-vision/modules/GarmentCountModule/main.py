# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import os
import asyncio
from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse, Message
import json
from datetime import datetime
from datetime import datetime, timezone

#For Speech
import time
import sys

async def main():
    # The client object is used to interact with your Azure IoT hub.
    module_client = IoTHubModuleClient.create_from_edge_environment()

    # connect the client.
    await module_client.connect()

    # event indicating when user is finished
    finished = threading.Event()
    
    counting = False; 
    total_count = 0;
    currentScanCount=0;
    

    # Define behavior for receiving an input message on input1 and input2
    # NOTE: this could be a coroutine or a function
    async def message_handler(input_message):
        global counting 
        global total_count
        global currentScanCount

        print(f'InputName[{input_message.input_name}]')
        now = datetime.now()
        if input_message.input_name == "CountInput":
            
            print(f'{now} The data in the message received on azureeyemodule was {input_message.data}')
            print(f'{now} Custom properties are {input_message.custom_properties})')

            inference_list = json.loads(input_message.data)['NEURAL_NETWORK']
            print(f'inference list: {inference_list}')
            count_garment = 0 
            
            if isinstance(inference_list, list) and inference_list:
                global counting 
                global currentScanCount
                now = datetime.fromtimestamp(int(inference_list[0]['timestamp'][:-9]))
                
                count_garment = len(inference_list)
                if counting:
                    currentScanCount =count_garment;

            print(f'Garment_Count: {count_garment}')
            print(f'Date: {now}')

            json_data = {
                    'Date': f'{now}', 
                    'Garment_Count': count_garment
                }
        
            print("forwarding mesage to output1")
            msg = Message(json.dumps(json_data))
            msg.content_encoding = "utf-8"
            msg.content_type = "application/json"
            await module_client.send_message_to_output(msg, "output1")
            
        elif input_message.input_name == "EarInput":
            print("Ear Input Received.")

            #input_message = module_client.receive_message_on_input("EarInput")
            print('input_message:')
            print(input_message)
            #text_data = input_message.data.decode('utf-8')
            text_data = input_message.data
            print(f'text_data :')
            print(text_data)
            dict_data = json.loads(text_data)
            #print("the data in the message received on input1 was ")
            #print(input_message.data)
            #print("the data text in the message received on input1 was ")
            #print(text_data)
            #print("the object in the message received on input1 was ")
            #print(dict_data)

            if 'botResponse' in dict_data:
                resp = dict_data['botResponse']
                print(f'resp: {resp}')

                if resp == 'Ok Got it.Counting Started':
                    print('Received Start.')
                    total_count = 0;
                    currentScanCount=0;
                    counting=True;
                    
                    countStart_data = {
                                        'Date': f'{now}', 
                                        'Data':'New Counting Started'
                                    }
                                
                    countStartMsg = Message(json.dumps(countStart_data))
                    countStartMsg.content_encoding = "utf-8"
                    countStartMsg.content_type = "application/json"
                    await module_client.send_message_to_output(countStartMsg, "output1")


                if resp == 'Counting Stopped':
                    total_count= total_count + currentScanCount
                    currentScanCount=0;
                    counting=False;

                    finalcount_data = {
                                        'Date': f'{now}', 
                                        'Total_Garment_Count': total_count
                                    }
                                
                    finalmsg = Message(json.dumps(finalcount_data))
                    finalmsg.content_encoding = "utf-8"
                    finalmsg.content_type = "application/json"
                    print(f'Total_Garment_Count[{finalcount_data}]')
                    await module_client.send_message_to_output(finalmsg, "output1")

                    print('Received Stop.')

                if resp == 'Please scan next set of garments':
                    total_count= total_count + currentScanCount
                    currentScanCount=0;
                    print('Received Next.')
                    next_data = {
                                        'Date': f'{now}', 
                                        'Data': 'Scaning Next Set'
                                }
                                
                    nextMsg = Message(json.dumps(next_data))
                    nextMsg.content_encoding = "utf-8"
                    nextMsg.content_type = "application/json"
                    await module_client.send_message_to_output(nextMsg, "output1")
                            

            #print("custom properties are")
            #print(input_message.custom_properties)
            #print("forwarding mesage to output1")
            #############################
        else:
            print("message received on unknown input")

    # Define behavior for receiving a twin desired properties patch
    # NOTE: this could be a coroutine or function
    def twin_patch_handler(patch):
        print("the data in the desired properties patch was: {}".format(patch))

    # Define behavior for receiving methods
    async def method_handler(method_request):
        print("Unknown method request received: {}".format(method_request.name))
        method_response = MethodResponse.create_from_method_request(method_request, 400, None)
        await module_client.send_method_response(method_response)

    # set the received data handlers on the client
    module_client.on_message_received = message_handler
    module_client.on_twin_desired_properties_patch_received = twin_patch_handler
    module_client.on_method_request_received = method_handler

    # This will trigger when a Direct Method Request for "shutdown" is sent.
    # NOTE: This sample will NOT exit until a Direct Method Request is sent.
    # Send one using the Azure IoT Explorer or the Azure IoT CLI
    # (https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-direct-methods)
    finished.wait()
    # Once it is received, shut down the client
    await module_client.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

    # If using Python 3.6 or below, use the following code instead of asyncio.run(main()):
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # loop.close()


#ForSpeech Module

""" 
async def SpeechMain(module_client,finished):
    
    try:

        # define behavior for receiving an input message on input1
        async def input1_listener(module_client):
            while True:
                input_message = await module_client.receive_message_on_input("EarInput")  # blocking call
                text_data = input_message.data.decode('utf-8')
                dict_data = json.loads(text_data)
                

                print("the data in the message received on input1 was ")
                print(input_message.data)
                print("the data text in the message received on input1 was ")
                print(text_data)
                print("the object in the message received on input1 was ")
                print(dict_data)

                if 'botResponse' in dict_data:
                    resp = dict_data["botResponse"]
                    print(f'resp: {resp}')

                    if resp == 'Ok Starting now. Please Start scanning your selected garments':
                        print('Received Start.')
                        
                    if resp == 'Stopped Scanning.':
                        print('Received Stop.')
                
                    if resp == 'Please scan your next set of garments.':
                        print('Received Next.')
                

                print("custom properties are")
                print(input_message.custom_properties)
                print("forwarding mesage to output1")
                await module_client.send_message_to_output(input_message, "output1")

        # Schedule task for C2D Listener
        listeners = asyncio.gather(input1_listener(module_client))

        print ( "waiting for Command/messages. ")
     
        finished.wait()

        # Cancel listening
        listeners.cancel()

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise

 """