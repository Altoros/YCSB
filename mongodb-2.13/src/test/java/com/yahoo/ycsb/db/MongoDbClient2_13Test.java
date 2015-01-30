package com.yahoo.ycsb.db;

import junit.framework.Assert;
import org.junit.Before;
import org.junit.Test;

import java.util.Properties;

public class MongoDbClient2_13Test {
    private MongoDbClient2_13 client;
    private Properties properties;

    @Before
    public void setUp() {
        client = new MongoDbClient2_13();
        properties = new Properties();
    }

    @Test
    public void testInitDefaultUrl() throws Exception {
        client.init();
        Assert.assertEquals(MongoConfig.DEFAULT_URL, client.mongoConfig.getHosts());
    }

    @Test
    public void testInitOverrideUrl() throws Exception {
        String url = "mongodb://1.1.1.1:27017";
        properties.put(MongoConfig.URL, url);
        client.setProperties(properties);
        client.init();
        Assert.assertEquals(url, client.mongoConfig.getHosts());
    }
}
