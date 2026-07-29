CREATE TABLE salons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    open_time TIME,
    close_time TIME
);

CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price INTEGER NOT NULL
);

CREATE TABLE masters (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    salon_id INTEGER NOT NULL REFERENCES salons(id)
);

CREATE TABLE master_services (
    master_id INTEGER NOT NULL REFERENCES masters(id),
    service_id INTEGER NOT NULL REFERENCES services(id),

    PRIMARY KEY (master_id, service_id)
);

CREATE TABLE clients (
    id BIGINT PRIMARY KEY,
    full_name VARCHAR(100),
    phone VARCHAR(20)
);

CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    client_id BIGINT REFERENCES clients(id),
    master_id INTEGER REFERENCES masters(id),
    service_id INTEGER REFERENCES services(id),

    appointments_date DATE,
    appointments_time TIME,

    status VARCHAR(20)
);

