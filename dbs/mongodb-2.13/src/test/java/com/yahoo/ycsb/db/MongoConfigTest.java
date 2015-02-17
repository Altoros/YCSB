package com.yahoo.ycsb.db;

import junit.framework.Assert;
import org.junit.Before;
import org.junit.Test;

import java.util.Properties;

public class MongoConfigTest {
    private MongoConfig config;
    private Properties properties;

    @Before
    public void setUp() {
        properties = new Properties();
        config = new MongoConfig(properties);
    }

    @Test
    public void testGetHostsOverrideURL() {
        String host = "mongodb://1.1.1.1:27017";
        properties.put(MongoConfig.URL, host);
        Assert.assertEquals(host, config.getHosts());
    }

    @Test
    public void testGetHostsDefaultURL() {
        Assert.assertEquals(MongoConfig.DEFAULT_URL, config.getHosts());
    }
}
