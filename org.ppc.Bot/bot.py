'''
Created on March 27, 2017

This file is subject to the terms and conditions defined in the
file 'LICENSE.txt', which is part of this source code package.

@author: David Moss
'''

import json

import localization

from organization.organization import Organization
import utilities.utilities as utilities

def run(botengine):
    """
    Entry point for bot microservices
    :param botengine: BotEngine environment object, our window to the outside world.
    """
    localization.initialize(botengine)

    #===========================================================================
    print("INPUTS: " + json.dumps(botengine.get_inputs(), indent=2, sort_keys=True))
    #===========================================================================
    trigger_type = botengine.get_trigger_type()
    triggers = botengine.get_triggers()
    botengine.get_logger().info("TRIGGER : " + str(trigger_type))
    
    # Grab our non-volatile memory
    organization = load_organization(botengine)

    executed = False

    # SCHEDULE TRIGGER
    if trigger_type & botengine.TRIGGER_SCHEDULE != 0:
        executed = True
        schedule_id = "DEFAULT"
        if 'scheduleId' in botengine.get_inputs():
            schedule_id = botengine.get_inputs()['scheduleId']

        organization.schedule_fired(botengine, schedule_id)

    # QUESTIONS ANSWERED
    if trigger_type & botengine.TRIGGER_QUESTION_ANSWER != 0:
        executed = True
        question = botengine.get_answered_question()
        botengine.get_logger().info("Answered: " + str(question.key_identifier))
        botengine.get_logger().info("Answer = {}".format(question.answer))
        organization.question_answered(botengine, question)
        
    # DATA STREAM TRIGGERS
    if trigger_type & botengine.TRIGGER_DATA_STREAM != 0:
        executed = True
        data_stream = botengine.get_datastream_block()
        botengine.get_logger().info("Data Stream: " + json.dumps(data_stream, sort_keys=True))
        if 'address' not in data_stream:
            botengine.get_logger().warn("Data stream message does not contain an 'address' field. Ignoring the message.")
            
        else:
            address = data_stream['address']

            if 'feed' in data_stream:
                content = data_stream['feed']
            else:
                content = {}

            if 'fromAppInstanceId' in data_stream:
                if type(content) == type({}):
                    content['sender_bot_id'] = data_stream['fromAppInstanceId']

            organization.datastream_updated(botengine, address, content)

    # DATA REQUEST
    if trigger_type & botengine.TRIGGER_DATA_REQUEST != 0:
        executed = True
        botengine.get_logger().info("Data request received")
        data = botengine.get_data_block()
        events = {}
        imported = False

        import importlib
        try:
            import lz4.block
            imported = True
        except ImportError:
            botengine.get_logger().error("Attempted to import 'lz4' to uncompress the data request response, but lz4 is not available. Please add 'lz4' to 'pip_install_remotely' in your structure.json.")
            pass

        if imported:
            for d in data:
                reference = None
                if 'key' in d:
                    reference = d['key']

                if reference not in events:
                    events[reference] = {}

                botengine.get_logger().info("Downloading {} bytes...".format(d['compressedLength']))
                r = botengine._requests.get(d['url'], timeout=60, stream=True)
                data = lz4.block.decompress(r.content, uncompressed_size=d['dataLength'])

                if d['type'] == botengine.DATA_REQUEST_TYPE_LOCATIONS:
                    headers_raw = data.decode('utf-8').split('\n')[0].strip().split(",")
                    headers = []
                    import re
                    for h in headers_raw:
                        # Transform CamelCase to snake_case
                        headers.append(re.sub(r'(?<!^)(?=[A-Z])', '_', h).lower())

                    data = data.decode('utf-8').split('\n')[1:]

                    # formated[location_id] = {'timezone': __, 'creation_time': __, 'event': __, 'organization_id': __, 'group_id': __}
                    formatted = {}

                    # Here we go line-by-line and transform CSV strings into a dictionary of headers : values.
                    for line in data:
                        if line != "":
                            l = line.strip().split(",")
                            processed = {}
                            for index, header in enumerate(headers):
                                processed[header] = utilities.normalize_measurement(l[index])

                            location_id = processed['id']
                            del processed['id']
                            formatted[location_id] = processed

                    events[reference] = formatted

                elif d['type'] == botengine.DATA_REQUEST_TYPE_DEVICES:
                    headers_raw = data.decode('utf-8').split('\n')[0].strip().split(",")
                    headers = []
                    import re
                    for h in headers_raw:
                        headers.append(re.sub(r'(?<!^)(?=[A-Z])', '_', h).lower())

                    data = data.decode('utf-8').split('\n')[1:]

                    botengine.get_logger().info("HEADERS: {}".format(headers))

                    # formatted[location_id][device_id] = { ... }
                    formatted = {}

                    # Here we go line-by-line and transform CSV strings into a dictionary of headers : values.
                    for line in data:
                        if line != "":
                            l = line.strip().split(",")
                            processed = {}
                            for index, header in enumerate(headers):
                                processed[header] = utilities.normalize_measurement(l[index])

                            location_id = int(processed['location_id'])
                            del processed['location_id']

                            device_id = processed['device_id']
                            del processed['device_id']

                            formatted[location_id] = { device_id : processed }

                    events[reference] = formatted

                else:
                    events[reference] = data

            for reference in events:
                organization.data_request_ready(botengine, reference, events[reference])

        # DO NOT SAVE CORE VARIABLES HERE.
        return

    if not executed:
        botengine.get_logger().error("bot.py: Unknown trigger {}".format(trigger_type))
    
    # Always save your variables!
    botengine.save_variable("organization", organization, required_for_each_execution=True)
    botengine.get_logger().info("<< bot")
    
    
    
def load_organization(botengine):
    """
    Load the organization object
    :param botengine: Execution environment
    """
    logger = botengine.get_logger()
    try:
        organization = botengine.load_variable("organization")
        logger.info("Loaded the organization")

    except:
        organization = None
        logger.info("Unable to load the organization")

    if organization == None:
        botengine.get_logger().info("Bot : Creating a new organization object. Hello.")
        organization_id = botengine.get_inputs()['organization']['organizationId']
        botengine.get_logger().info("Organization ID is {}.".format(organization_id))

        organization = Organization(botengine, organization_id)
        botengine.save_variable("organization", organization, required_for_each_execution=True)

        try:
            import signals.analytics as analytics
            analytics.track(botengine, organization, 'reset')

        except ImportError:
            pass

    organization.initialize(botengine)
    return organization


# ===============================================================================
# Organization Intelligence Timers
# ===============================================================================
def _organization_intelligence_fired(botengine, argument_tuple):
    """
    Entry point into this bot
    Location intelligence timer or alarm fired
    :param botengine: BotEngine Environment
    :param argument_tuple: (intelligence_id, argument)
    """
    botengine.get_logger().info("\n\nTRIGGER : _organization_intelligence_fired()")
    organization = load_organization(botengine)
    organization.timer_fired(botengine, argument_tuple[0], argument_tuple[1])
    botengine.save_variable("organization", organization, required_for_each_execution=True)
    botengine.get_logger().info("<< bot (location timer)")


def start_organization_intelligence_timer(botengine, seconds, intelligence_id, argument, reference):
    """
    Start a relative location intelligence timer
    :param botengine: BotEngine environment
    :param seconds: Seconds from the start of the current execution to make this timer fire
    :param intelligence_id: ID of the intelligence module to trigger when this timer fires
    :param argument: Arbitrary argument to pass into the intelligence module's timer_fired() method when this timer fires
    :param reference: Unique reference name that lets us later cancel this timer if needed
    """
    botengine.get_logger().info(">start_organization_intelligence_timer({}, {})".format(seconds, reference))
    if reference is not None and reference != "":
        botengine.cancel_timers(reference)
    botengine.start_timer_s(int(seconds), _organization_intelligence_fired, (intelligence_id, argument), reference)


def start_organization_intelligence_timer_ms(botengine, milliseconds, intelligence_id, argument, reference):
    """
    Start a relative location intelligence timer
    :param botengine: BotEngine environment
    :param milliseconds: Milliseconds from the start of the current execution to make this timer fire
    :param intelligence_id: ID of the intelligence module to trigger when this timer fires
    :param argument: Arbitrary argument to pass into the intelligence module's timer_fired() method when this timer fires
    :param reference: Unique reference name that lets us later cancel this timer if needed
    """
    botengine.get_logger().info(">start_organization_intelligence_timer_ms({}, {})".format(milliseconds, reference))
    if reference is not None and reference != "":
        botengine.cancel_timers(reference)
    botengine.start_timer_ms(int(milliseconds), _organization_intelligence_fired, (intelligence_id, argument), reference)


def set_organization_intelligence_alarm(botengine, timestamp_ms, intelligence_id, argument, reference):
    """
    Set an absolute location intelligence alarm
    :param botengine: BotEngine environment
    :param timestamp: Absolute timestamp in milliseconds at which to trigger this alarm
    :param intelligence_id: ID of the intelligence module to trigger when this alarm fires
    :param argument: Arbitrary argument to pass into the intelligence module's timer_fired() method when this timer fires
    :param reference: Unique reference name that lets us later cancel this timer if needed
    """
    botengine.get_logger().info(">set_organization_intelligence_alarm({})".format(timestamp_ms))
    if reference is not None and reference != "":
        botengine.cancel_timers(reference)
    botengine.set_alarm(int(timestamp_ms), _organization_intelligence_fired, (intelligence_id, argument), reference)


def cancel_organization_intelligence_timers(botengine, reference):
    """
    Cancel all location intelligence timers and alarms with the given reference
    :param botengine: BotEngine environment
    :param reference: Unique reference name for which to cancel all timers and alarms
    """
    botengine.cancel_timers(reference)


def is_organization_timer_running(botengine, reference):
    """
    Determine if the timer with the given reference is running
    :param botengine: BotEngine environment
    :param reference: Unique reference name for the timer
    :return: True if the timer is running
    """
    return botengine.is_timer_running(reference)

