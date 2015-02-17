package com.yahoo.ycsb.db;

import com.mongodb.WriteConcern;
import org.junit.Before;
import org.junit.Test;

import java.util.Properties;

import static org.junit.Assert.assertEquals;

public class MongoDbClientTest {

    private MongoDbClient client;
    private Properties props;

    @Before
    public void setUp() {
        client = new MongoDbClient();
        props = new Properties();
    }

    public void nullifyMongos() {
        MongoDbClient.mongos = null;
    }

    @Test
    public void testInitWriteConcernDefault() throws Exception {
        nullifyMongos();
        client.init();
        assertEquals(WriteConcern.JOURNALED, MongoDbClient.writeConcern);
    }

    @Test
    public void testInitWriteConcernNormal() throws Exception {
        nullifyMongos();
        props.setProperty("mongodb.writeConcern", "unacknowledged");
        client.setProperties(props);
        client.init();
        assertEquals(WriteConcern.UNACKNOWLEDGED, MongoDbClient.writeConcern);
    }

}
