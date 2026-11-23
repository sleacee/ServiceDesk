
create table role (
    role_id integer generated always as identity primary key,
    name varchar(50) not null unique,
    description varchar(255)
);

create table employee (
    employee_id integer generated always as identity primary key,
    role_id integer not null references role(role_id),
    full_name varchar(150) not null,
    phone varchar(20),
    email varchar(100)
);

create table client (
    client_id integer generated always as identity primary key,
    full_name varchar(150) not null,
    phone varchar(20) not null,
    email varchar(100)
);

create table equipment (
    equipment_id integer generated always as identity primary key,
    client_id integer not null references client(client_id),
    type varchar(50) not null,
    brand varchar(50) not null,
    model varchar(100) not null,
    serial_number varchar(100)
);

create table service_order (
    order_id integer generated always as identity primary key,
    equipment_id integer not null references equipment(equipment_id),
    employee_id integer references employee(employee_id),
    created_by_employee_id integer not null references employee(employee_id),
    created_at timestamp not null default current_timestamp,
    status varchar(30) not null,
    problem_description text not null
);

create table diagnosis (
    diagnosis_id integer generated always as identity primary key,
    order_id integer not null unique references service_order(order_id),
    employee_id integer not null references employee(employee_id),
    description text not null,
    repair_cost decimal(10,2) not null check (repair_cost >= 0),
    estimated_completion timestamp
);

create table part (
    part_id integer generated always as identity primary key,
    name varchar(150) not null,
    article varchar(50) not null unique,
    price decimal(10,2) not null check (price >= 0),
    quantity integer not null default 0 check (quantity >= 0)
);

create table payment (
    payment_id integer generated always as identity primary key,
    order_id integer not null unique references service_order(order_id),
    amount decimal(10,2) not null check (amount > 0),
    payment_date timestamp not null default current_timestamp,
    payment_method varchar(30) not null,
    status varchar(30) not null
);

create table order_part (
    order_part_id integer generated always as identity primary key,
    order_id integer not null references service_order(order_id),
    part_id integer not null references part(part_id),
    quantity integer not null check (quantity > 0),
    price decimal(10,2) not null check (price >= 0)
);
