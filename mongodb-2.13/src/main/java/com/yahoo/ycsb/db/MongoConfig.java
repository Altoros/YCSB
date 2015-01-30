package com.yahoo.ycsb.db;

import com.mongodb.ReadPreference;
import com.mongodb.WriteConcern;
import com.yahoo.ycsb.config.PropertiesConfig;

import java.util.Properties;

public class MongoConfig extends PropertiesConfig {

    public static final String URL = "mongodb.url";
    
    public static final String DEFAULT_URL = "mongodb://localhost:27017";

    public static final String DATABASE = "mongodb.database";

    public static final String DEFAULT_DATABASE = "ycsb";

    public static final String SHUTDOWN_TIMEOUT_MILLIS_PROPERTY = "mongodb.shutdownTimeoutMillis";
    public static final long DEFAULT_SHUTDOWN_TIMEOUT_MILLIS = 30000;

    public static final String OBJECT_EXPIRATION_TIME_PROPERTY = "mongodb.objectExpirationTime";
    public static final int DEFAULT_OBJECT_EXPIRATION_TIME = Integer.MAX_VALUE;

    public static final String CHECK_OPERATION_STATUS_PROPERTY = "mongodb.checkOperationStatus";
    public static final boolean CHECK_OPERATION_STATUS_DEFAULT = true;

    public static final long DEFAULT_OP_TIMEOUT = 60000;
    public static final String OP_TIMEOUT_PROPERTY = "mongodb.opTimeout";

    public static final String READ_BUFFER_SIZE_PROPERTY = "mongodb.readBufferSize";
    public static final int READ_BUFFER_SIZE_DEFAULT = 16384;

    public static final String WRITE_CONCERN= "mongodb.writeConcern";
    public static final WriteConcern WRITE_CONCERN_DEFAULT = WriteConcern.JOURNALED;

    public static final String THREAD_COUNT = "threadcount";
    public static final Integer THREAD_COUNT_DEFAULT = 100;

    public static final String READ_PREFERENCE = "mongodb.readPreference";
    public static final ReadPreference READ_PREFERENCE_DEFAULT = ReadPreference.primary();

    public static final String W_PARAMETER = "mongodb.w";
    public static final int W_PARAMETER_DEFAULT  = 1;

    public static final String WTIMEOUT_PARAMETER = "mongodb.wtimeout";
    public static final int WTIMEOUT_PARAMETER_DEFAULT  = 0;

    public static final String FSYNC_PARAMETER = "mongodb.fsync";
    public static final boolean FSYNC_PARAMETER_DEFAULT  = false;

    public static final String J_PARAMETER = "mongodb.j";
    public static final boolean J_PARAMETER_DEFAULT  = true;


    public MongoConfig(Properties properties) {
        super(properties);
        declareProperty(URL, DEFAULT_URL, true);
        declareProperty(DATABASE, DEFAULT_DATABASE);
        declareProperty(CHECK_OPERATION_STATUS_PROPERTY, CHECK_OPERATION_STATUS_DEFAULT);
        declareProperty(OP_TIMEOUT_PROPERTY, DEFAULT_OP_TIMEOUT);
        declareProperty(READ_BUFFER_SIZE_PROPERTY, READ_BUFFER_SIZE_DEFAULT);
        declareProperty(SHUTDOWN_TIMEOUT_MILLIS_PROPERTY, DEFAULT_SHUTDOWN_TIMEOUT_MILLIS);
        declareProperty(OBJECT_EXPIRATION_TIME_PROPERTY, DEFAULT_OBJECT_EXPIRATION_TIME);
        declareProperty(WRITE_CONCERN, false);
        declareProperty(THREAD_COUNT, THREAD_COUNT_DEFAULT);
        declareProperty(READ_PREFERENCE, READ_PREFERENCE_DEFAULT);
        declareProperty(W_PARAMETER, W_PARAMETER_DEFAULT);
        declareProperty(WTIMEOUT_PARAMETER, WTIMEOUT_PARAMETER_DEFAULT);
        declareProperty(FSYNC_PARAMETER, FSYNC_PARAMETER_DEFAULT, false);
        declareProperty(J_PARAMETER, J_PARAMETER_DEFAULT, false);
    }

    public String getHosts() {
        return getString(URL);
    }

    public String getDatabase() {
        return getString(DATABASE);
    }

    public WriteConcern getWriteConcern() {
        String writeConcernValue = getProperty(WRITE_CONCERN);
        WriteConcern writeConcern = null;
        try {
            if (writeConcernValue != null) {
                writeConcern = WriteConcern.valueOf(writeConcernValue);
            } else {
                writeConcern = new WriteConcern(getWParameter(), getWtimeoutParameter(), getFsyncParameter(), getJParameter());
            }
        } catch (Exception ex) {
            System.err.println("ERROR: Invalid writeConcern: '"
                    + getString(WRITE_CONCERN)
                    + "'. "
                    + "Must be [ errors_ignored | unacknowledged | acknowledged | journaled | replica_acknowledged ]");
            System.exit(1);
        }
        return writeConcern;
    }

    public Integer getThreadCount(){
        return getInteger(THREAD_COUNT);
    }

    public ReadPreference getReadPreference () {
        ReadPreference result = null;
        String readPreference = getProperty(READ_PREFERENCE);
        try {
            result =  readPreference != null ?
                    ReadPreference.valueOf(readPreference) :
                    this.<ReadPreference>getDefaultValue(READ_PREFERENCE);
        } catch (Exception e) {
            System.err.println("ERROR: Invalid readPreference: '"
                    + readPreference
                    + "'. Must be [ primary | primaryPreferred | secondary | secondaryPreferred | nearest ]");
            System.exit(1);
        }
        return result;
    }

    public Integer getWParameter () {
         return getInteger(W_PARAMETER);
    }

    public Integer getWtimeoutParameter () {
        return getInteger(WTIMEOUT_PARAMETER);
    }

    public Boolean getFsyncParameter () {
        return getBoolean(FSYNC_PARAMETER);
    }

    public Boolean getJParameter () {
        return getBoolean(J_PARAMETER);
    }

}
