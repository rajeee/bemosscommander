
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from webapps.deviceinfos.models import DeviceMetadata
from webapps.device.models import Devicedata
from bemoss_lib.utils.VIP_helper import vip_publish
from bemoss_lib.utils.BEMOSS_ONTOLOGY import BEMOSS_ONTOLOGY
from django.core.exceptions import ObjectDoesNotExist
import json
import settings


ALEXAKEY = settings.ALEXA_KEY

@api_view(['GET', 'POST'])
def device_monitor(request):
    print "device_monitor"
    print request.data
    if request.data['auth'] == ALEXAKEY:
        if request.method == 'POST':
            received_data = request.data
            if isinstance(received_data, dict):
                data = json.loads(received_data['dumps'])
            else:
                myDict = dict(received_data.iterlists())
                data = dict()
                for key, value in myDict.iteritems():
                    data[key.encode('utf8')] = value[0].encode('utf8')
            device_nickname = data['nickname']
            try:
                device_info = DeviceMetadata.objects.get(nickname=device_nickname)
            except ObjectDoesNotExist:
                response = {'success': 0, 'cause': 'No such device found'}
                return Response(response)
            agent_id = device_info.agent_id
            device_data = Devicedata.objects.get(agent_id=agent_id).data
            if 'variable' in data.keys():
                try:
                    var = data['variable']
                    if var == '':
                        response = {'success': 0, 'cause': 'Empty variable.'}
                    elif var == 'setpoint':
                        mode = device_data[BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME]
                        if mode == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.HEAT:
                            response = {'success': 1, 'value': device_data[BEMOSS_ONTOLOGY.HEAT_SETPOINT.NAME]}
                        else:
                            response = {'success': 1, 'value': device_data[BEMOSS_ONTOLOGY.COOL_SETPOINT.NAME]}
                    else:
                        try:
                            response = {'success': 1, 'value': device_data[var]}
                        except KeyError:
                            var = var.replace(' ', '_')
                            var = var.replace('set_point', 'setpoint')
                            response = {'success': 1, 'value': device_data[var]}
                    return Response(response)
                except KeyError:
                    response = {'success': 0, 'cause': 'variable does not exist'}
                    return Response(response)
            else:
                response = {'success': 1}
                response.update({'value': device_data})
                return Response(response)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        response = {'success': 0, 'cause': 'Unauthorized!'}
        return Response(response)


@api_view(['POST', 'GET'])
def device_control(request):
    print "device_control"
    print request.data
    if request.data['auth'] == ALEXAKEY:
        if request.method == 'POST':
            data=dict()
            failed_variables=list()
            senddata=dict()
            received_data=request.data
            # myDict=dict(received_data.iterlists())
            # for key,value in myDict.iteritems():
            #     data[key.encode('utf8')]=value[0].encode('utf8')
            data = json.loads(received_data['dumps'])
            nickname = data['nickname']
            try:
                device_info = DeviceMetadata.objects.get(nickname=nickname)
            except ObjectDoesNotExist:
                response = {'success': 0, 'cause': 'No such device found'}
                return Response(response)
            agent_id = device_info.agent_id
            validdata = False
            device_data = Devicedata.objects.get(agent_id=agent_id).data
            if device_info == '':
                response = {'success':0, 'cause':'No such device found'}
                return Response(response)
            variables = json.loads(json.dumps(data['variable']))
            for variable in variables.keys():
                val = variables[variable]
                variable = variable.replace(' ', '_')
                variable = variable.replace('set_point', 'setpoint')
                if variable not in device_data.keys():
                    message = "invalid attribute selected to change"
                    failed_variables.append(variable)
                    continue
                elif variable == "setpoint":
                        validdata = True
                        mode = device_data[BEMOSS_ONTOLOGY.THERMOSTAT_MODE.NAME]
                        if mode == BEMOSS_ONTOLOGY.THERMOSTAT_MODE.POSSIBLE_VALUES.HEAT:
                            senddata[BEMOSS_ONTOLOGY.HEAT_SETPOINT.NAME] = val
                        else:
                            senddata[BEMOSS_ONTOLOGY.COOL_SETPOINT.NAME] = val
                else:
                    validdata = True
                    senddata[variable] = val

            update_send_topic = 'to/' + agent_id + '/from/ui/update'
            update_send_topic2 = 'to/' + agent_id + '/update/from/ui'
            print update_send_topic
            vip_publish(update_send_topic, senddata)
            vip_publish(update_send_topic2, senddata)
            if failed_variables:
                if validdata:
                    response = {'success':2,'cause':'One or more variable invalid'}
                else:
                    response = {'success': 0, 'cause': 'invalid variables'}
                return Response(response)
            response = {'success': 1}
            return Response(response)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        response = {'success': 0, 'cause': 'Unauthorized!'}
        return Response(response)
