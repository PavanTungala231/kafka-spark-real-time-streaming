'''
This simple code illustrates a Kafka producer:
- read data from a CSV file. Use the data from
    https://github.com/rdsea/bigdataplatforms/tree/master/data/onudata
- for each data record, produce a json record
- send the json record to a Kafka messaging system

We use python client library from https://docs.confluent.io/clients-confluent-kafka-python/current/overview.html.
Also see https://github.com/confluentinc/confluent-kafka-python
'''
import argparse
from confluent_kafka import Producer
import pandas as pd
import json
import time
import datetime


'''
A common, known function used for jsonifying a timestamp into a string
'''


def datetime_converter(dt):
    if isinstance(dt, datetime.datetime):
        return dt.__str__()


'''
A common way to get the error if something is wrong with
the delivery
'''


def kafka_delivery_error(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')


## Replace the information with your real kafka

'''
Check other documents for starting Kafka, e.g.
see https://github.com/rdsea/bigdataplatforms/tree/master/tutorials/basickafka
$docker-compose -f docker-compose3.yml up
'''

'''
The following code emulates the situation that we have real time data to be sent to kafka
'''
if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--broker', default="localhost:19092", help='Broker as "server:port"')
    parser.add_argument('-i', '--input_file', help='Input file')
    parser.add_argument('-c', '--chunksize', help='chunk size for big file')
    parser.add_argument('-s', '--sleeptime', help='sleep time in second')
    parser.add_argument('-t', '--topic', help='kafka topic')
    parser.add_argument('--security_protocol', default='SASL_PLAINTEXT', help='security protocol')
    parser.add_argument('--sasl_mechanism', default='PLAIN', help='security protocol')
    parser.add_argument('--sasl_username', help='sasl user name')
    parser.add_argument('--sasl_password', help='sasl password')
    args = parser.parse_args()

    '''
    Because the KPI file is big, we emulate by reading chunk, using iterator and chunksize
    '''
    INPUT_DATA_FILE = args.input_file
    chunksize = int(args.chunksize)
    sleeptime = int(args.sleeptime)
    KAFKA_TOPIC = args.topic

    # create configuration file for kafka connection
    if (args.sasl_username is None) and (args.sasl_password is None):
        kafka_conf = {
            'bootstrap.servers': args.broker
        }
    else:
        kafka_conf = {
            'bootstrap.servers': args.broker,
            'security.protocol': args.security_protocol,
            'sasl.mechanism': args.sasl_mechanism,
            'sasl.username': args.sasl_username,
            'sasl.password': args.sasl_password
        }
    '''
    the time record is "TIME"
    we read data by chunk so we can handle a big sample data file
    '''
    input_data = pd.read_csv(INPUT_DATA_FILE, iterator=True, chunksize=chunksize, header=0, names=[
        "trip_id",
        "taxi_id",
        "trip_start_timestamp",
        "trip_end_timestamp",
        "trip_seconds",
        "trip_miles",
        "pickup_census_tract",
        "dropoff_census_tract",
        "pickup_community_area",
        "dropoff_community_area",
        "fare",
        "tips",
        "tolls",
        "extras",
        "trip_total",
        "payment_type",
        "company",
        "pickup_centroid_latitude",
        "pickup_centroid_longitude",
        "pickup_centroid_location",
        "dropoff_centroid_latitude",
        "dropoff_centroid_longitude",
        "dropoff_centroid_location"
    ])

    kafka_producer = Producer(kafka_conf)
    for chunk_data in input_data:
        '''
        now process each chunk
        '''
        chunk = chunk_data.dropna()
        chunk['event_timestamp'] = datetime.datetime.now()
        for index, row in chunk.iterrows():
            '''
            Assume that when some data is available, we send it to Kafka in JSON
            '''
            json_data = json.dumps(row.to_dict(), default=datetime_converter)
            # check if any event/error sent
            print(json_data.encode('utf-8'))
            kafka_producer.produce(KAFKA_TOPIC, json_data.encode('utf-8'), callback=kafka_delivery_error)
            kafka_producer.flush()
            # sleep a while, if needed as it is an emulation
            time.sleep(sleeptime)
