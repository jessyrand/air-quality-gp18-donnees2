CREATE TABLE IF NOT EXISTS dim_city (
    city_id     SERIAL PRIMARY KEY,
    city_name   TEXT NOT NULL UNIQUE,
    country     TEXT,
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS dim_time (
    time_id         SERIAL PRIMARY KEY,
    full_datetime   TIMESTAMPTZ NOT NULL UNIQUE,
    date            DATE NOT NULL,
    hour            SMALLINT NOT NULL,
    day_of_week     TEXT NOT NULL,
    is_weekend      BOOLEAN NOT NULL,
    month           SMALLINT NOT NULL,
    year            SMALLINT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_aqi (
    fact_id             SERIAL PRIMARY KEY,
    city_id             INTEGER NOT NULL REFERENCES dim_city(city_id),
    time_id             INTEGER NOT NULL REFERENCES dim_time(time_id),
    pm10                DOUBLE PRECISION,
    pm2_5               DOUBLE PRECISION,
    carbon_monoxide     DOUBLE PRECISION,
    carbon_dioxide      DOUBLE PRECISION,
    nitrogen_dioxide    DOUBLE PRECISION,
    sulphur_dioxide     DOUBLE PRECISION,
    ozone               DOUBLE PRECISION,
    methane             DOUBLE PRECISION,
    european_aqi        DOUBLE PRECISION,
    us_aqi              DOUBLE PRECISION,
    UNIQUE (city_id, time_id)
);