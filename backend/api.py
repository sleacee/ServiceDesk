from fastapi import FastAPI, HTTPException
from database import get_connection
from psycopg.rows import dict_row

app = FastAPI(
    title="ServiceDesk API",
    description="REST API for a service center management system",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "ServiceDesk API is running"}

@app.get("/db-test")
def test_database():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select version()")
            result = cursor.fetchone()

    return {"database_version": result[0]}

@app.get("/clients")
def get_clients():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    client_id,
                    full_name,
                    phone,
                    email
                from client
                order by client_id
            """)
            clients = cursor.fetchall()

    return clients

@app.get("/clients/{client_id}")
def get_client(client_id: int):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    client_id,
                    full_name,
                    phone,
                    email
                from client
                where client_id = %s
            """, (client_id,))
            client = cursor.fetchone()

    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    return client

@app.post("/clients", status_code=201)
def create_client(client: dict):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                insert into client (full_name, phone, email)
                values (%s, %s, %s)
                returning client_id, full_name, phone, email
            """, (
                client["full_name"],
                client["phone"],
                client.get("email")
            ))
            new_client = cursor.fetchone()

    return new_client

@app.put("/clients/{client_id}")
def update_client(client_id: int, client: dict):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                update client
                set
                    full_name = %s,
                    phone = %s,
                    email = %s
                where client_id = %s
                returning client_id, full_name, phone, email
            """, (
                client["full_name"],
                client["phone"],
                client.get("email"),
                client_id
            ))
            updated_client = cursor.fetchone()

    if updated_client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    return updated_client


@app.delete("/clients/{client_id}")
def delete_client(client_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                select client_id
                from client
                where client_id = %s
            """, (client_id,))

            existing_client = cursor.fetchone()

            if existing_client is None:
                raise HTTPException(
                    status_code=404,
                    detail="Client not found"
                )

            cursor.execute("""
                select equipment_id
                from equipment
                where client_id = %s
                limit 1
            """, (client_id,))

            if cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete client because related equipment exists"
                )

            cursor.execute("""
                delete from client
                where client_id = %s
            """, (client_id,))

    return {"message": "Client deleted successfully"}

@app.get("/equipment")
def get_equipment():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    equipment_id,
                    client_id,
                    type,
                    brand,
                    model,
                    serial_number
                from equipment
                order by equipment_id
            """)
            equipment = cursor.fetchall()

    return equipment

@app.get("/equipment/{equipment_id}")
def get_equipment_by_id(equipment_id: int):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    equipment_id,
                    client_id,
                    type,
                    brand,
                    model,
                    serial_number
                from equipment
                where equipment_id = %s
            """, (equipment_id,))
            equipment = cursor.fetchone()

    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment



@app.post("/equipment", status_code=201)
def create_equipment(equipment: dict):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                insert into equipment (
                    client_id,
                    type,
                    brand,
                    model,
                    serial_number
                )
                values (%s, %s, %s, %s, %s)
                returning
                    equipment_id,
                    client_id,
                    type,
                    brand,
                    model,
                    serial_number
            """, (
                equipment["client_id"],
                equipment["type"],
                equipment["brand"],
                equipment["model"],
                equipment.get("serial_number")
            ))
            new_equipment = cursor.fetchone()

    return new_equipment

@app.put("/equipment/{equipment_id}")
def update_equipment(equipment_id: int, equipment: dict):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                update equipment
                set
                    client_id = %s,
                    type = %s,
                    brand = %s,
                    model = %s,
                    serial_number = %s
                where equipment_id = %s
                returning
                    equipment_id,
                    client_id,
                    type,
                    brand,
                    model,
                    serial_number
            """, (
                equipment["client_id"],
                equipment["type"],
                equipment["brand"],
                equipment["model"],
                equipment.get("serial_number"),
                equipment_id
            ))
            updated_equipment = cursor.fetchone()

    if updated_equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return updated_equipment

@app.delete("/equipment/{equipment_id}")
def delete_equipment(equipment_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                select equipment_id
                from equipment
                where equipment_id = %s
            """, (equipment_id,))

            existing_equipment = cursor.fetchone()

            if existing_equipment is None:
                raise HTTPException(
                    status_code=404,
                    detail="Equipment not found"
                )

            cursor.execute("""
                select order_id
                from service_order
                where equipment_id = %s
                limit 1
            """, (equipment_id,))

            if cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete equipment because related orders exist"
                )

            cursor.execute("""
                delete from equipment
                where equipment_id = %s
            """, (equipment_id,))

    return {"message": "Equipment deleted successfully"}

@app.get("/orders")
def get_orders():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    so.order_id,
                    so.equipment_id,
                    so.employee_id,
                    so.created_by_employee_id,
                    so.created_at,
                    so.status,
                    so.problem_description,
                    e.type as equipment_type,
                    e.brand,
                    e.model,
                    c.client_id,
                    c.full_name as client_name
                from service_order so
                join equipment e on so.equipment_id = e.equipment_id
                join client c on e.client_id = c.client_id
                order by so.order_id
            """)
            orders = cursor.fetchall()

    return orders


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    so.order_id,
                    so.equipment_id,
                    so.employee_id,
                    so.created_by_employee_id,
                    so.created_at,
                    so.status,
                    so.problem_description,
                    e.type as equipment_type,
                    e.brand,
                    e.model,
                    c.client_id,
                    c.full_name as client_name
                from service_order so
                join equipment e on so.equipment_id = e.equipment_id
                join client c on e.client_id = c.client_id
                where so.order_id = %s
            """, (order_id,))
            order = cursor.fetchone()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return order

@app.post("/orders", status_code=201)
def create_order(order: dict):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                insert into service_order (
                    equipment_id,
                    employee_id,
                    created_by_employee_id,
                    status,
                    problem_description
                )
                values (%s, %s, %s, %s, %s)
                returning
                    order_id,
                    equipment_id,
                    employee_id,
                    created_by_employee_id,
                    created_at,
                    status,
                    problem_description
            """, (
                order["equipment_id"],
                order.get("employee_id"),
                order["created_by_employee_id"],
                order["status"],
                order["problem_description"]
            ))
            new_order = cursor.fetchone()

    return new_order

@app.put("/orders/{order_id}")
def update_order(order_id: int, order: dict):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                update service_order
                set
                    equipment_id = %s,
                    employee_id = %s,
                    created_by_employee_id = %s,
                    status = %s,
                    problem_description = %s
                where order_id = %s
                returning
                    order_id,
                    equipment_id,
                    employee_id,
                    created_by_employee_id,
                    created_at,
                    status,
                    problem_description
            """, (
                order["equipment_id"],
                order.get("employee_id"),
                order["created_by_employee_id"],
                order["status"],
                order["problem_description"],
                order_id
            ))
            updated_order = cursor.fetchone()

    if updated_order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return updated_order

@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                select order_id
                from service_order
                where order_id = %s
            """, (order_id,))

            existing_order = cursor.fetchone()

            if existing_order is None:
                raise HTTPException(
                    status_code=404,
                    detail="Order not found"
                )

            cursor.execute("""
                select diagnosis_id
                from diagnosis
                where order_id = %s
                limit 1
            """, (order_id,))

            if cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete order because related diagnosis exists"
                )

            cursor.execute("""
                select payment_id
                from payment
                where order_id = %s
                limit 1
            """, (order_id,))

            if cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete order because related payment exists"
                )

            cursor.execute("""
                select order_part_id
                from order_part
                where order_id = %s
                limit 1
            """, (order_id,))

            if cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete order because related parts exist"
                )

            cursor.execute("""
                delete from service_order
                where order_id = %s
            """, (order_id,))

    return {"message": "Order deleted successfully"}


@app.get("/employees")
def get_employees():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    e.employee_id,
                    e.role_id,
                    e.full_name,
                    e.phone,
                    e.email,
                    r.name as role_name
                from employee e
                join role r on e.role_id = r.role_id
                order by e.employee_id
            """)
            employees = cursor.fetchall()

    return employees


@app.get("/diagnoses")
def get_diagnoses():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    d.diagnosis_id,
                    d.order_id,
                    d.employee_id,
                    d.description,
                    d.repair_cost,
                    d.estimated_completion,
                    e.full_name as employee_name
                from diagnosis d
                join employee e on d.employee_id = e.employee_id
                order by d.diagnosis_id
            """)
            diagnoses = cursor.fetchall()

    return diagnoses


@app.get("/diagnoses/{diagnosis_id}")
def get_diagnosis(diagnosis_id: int):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    d.diagnosis_id,
                    d.order_id,
                    d.employee_id,
                    d.description,
                    d.repair_cost,
                    d.estimated_completion,
                    e.full_name as employee_name
                from diagnosis d
                join employee e on d.employee_id = e.employee_id
                where d.diagnosis_id = %s
            """, (diagnosis_id,))
            diagnosis = cursor.fetchone()

    if diagnosis is None:
        raise HTTPException(status_code=404, detail="Diagnosis not found")

    return diagnosis


@app.post("/diagnoses", status_code=201)
def create_diagnosis(diagnosis: dict):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select order_id
                from service_order
                where order_id = %s
            """, (diagnosis["order_id"],))

            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Order not found")

            cursor.execute("""
                select diagnosis_id
                from diagnosis
                where order_id = %s
            """, (diagnosis["order_id"],))

            if cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Diagnosis already exists for this order"
                )

            cursor.execute("""
                insert into diagnosis (
                    order_id,
                    employee_id,
                    description,
                    repair_cost,
                    estimated_completion
                )
                values (%s, %s, %s, %s, %s)
                returning
                    diagnosis_id,
                    order_id,
                    employee_id,
                    description,
                    repair_cost,
                    estimated_completion
            """, (
                diagnosis["order_id"],
                diagnosis["employee_id"],
                diagnosis["description"],
                diagnosis["repair_cost"],
                diagnosis.get("estimated_completion")
            ))
            new_diagnosis = cursor.fetchone()

    return new_diagnosis


@app.put("/diagnoses/{diagnosis_id}")
def update_diagnosis(diagnosis_id: int, diagnosis: dict):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                update diagnosis
                set
                    employee_id = %s,
                    description = %s,
                    repair_cost = %s,
                    estimated_completion = %s
                where diagnosis_id = %s
                returning
                    diagnosis_id,
                    order_id,
                    employee_id,
                    description,
                    repair_cost,
                    estimated_completion
            """, (
                diagnosis["employee_id"],
                diagnosis["description"],
                diagnosis["repair_cost"],
                diagnosis.get("estimated_completion"),
                diagnosis_id
            ))
            updated_diagnosis = cursor.fetchone()

    if updated_diagnosis is None:
        raise HTTPException(status_code=404, detail="Diagnosis not found")

    return updated_diagnosis


@app.get("/parts")
def get_parts():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    part_id,
                    name,
                    article,
                    price,
                    quantity
                from part
                order by part_id
            """)
            parts = cursor.fetchall()

    return parts


@app.get("/payments")
def get_payments():
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    payment_id,
                    order_id,
                    amount,
                    payment_date,
                    payment_method,
                    status
                from payment
                order by payment_id
            """)
            payments = cursor.fetchall()

    return payments


@app.get("/payments/{payment_id}")
def get_payment(payment_id: int):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    payment_id,
                    order_id,
                    amount,
                    payment_date,
                    payment_method,
                    status
                from payment
                where payment_id = %s
            """, (payment_id,))
            payment = cursor.fetchone()

    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    return payment


@app.post("/payments", status_code=201)
def create_payment(payment: dict):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select order_id
                from service_order
                where order_id = %s
            """, (payment["order_id"],))

            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Order not found")

            cursor.execute("""
                select payment_id
                from payment
                where order_id = %s
            """, (payment["order_id"],))

            if cursor.fetchone() is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Payment already exists for this order"
                )

            cursor.execute("""
                insert into payment (
                    order_id,
                    amount,
                    payment_method,
                    status
                )
                values (%s, %s, %s, %s)
                returning
                    payment_id,
                    order_id,
                    amount,
                    payment_date,
                    payment_method,
                    status
            """, (
                payment["order_id"],
                payment["amount"],
                payment["payment_method"],
                payment["status"]
            ))
            new_payment = cursor.fetchone()

    return new_payment


@app.get("/orders/{order_id}/parts")
def get_order_parts(order_id: int):
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select
                    op.order_part_id,
                    op.order_id,
                    op.part_id,
                    p.name as part_name,
                    p.article,
                    op.quantity,
                    op.price,
                    op.quantity * op.price as total_price
                from order_part op
                join part p on op.part_id = p.part_id
                where op.order_id = %s
                order by op.order_part_id
            """, (order_id,))
            order_parts = cursor.fetchall()

    return order_parts


@app.post("/orders/{order_id}/parts", status_code=201)
def add_order_part(order_id: int, order_part: dict):
    quantity = order_part["quantity"]

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                select order_id
                from service_order
                where order_id = %s
            """, (order_id,))

            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Order not found")

            cursor.execute("""
                select part_id, name, price, quantity
                from part
                where part_id = %s
                for update
            """, (order_part["part_id"],))

            part = cursor.fetchone()

            if part is None:
                raise HTTPException(status_code=404, detail="Part not found")

            if part["quantity"] < quantity:
                raise HTTPException(
                    status_code=409,
                    detail="Insufficient part quantity"
                )

            cursor.execute("""
                update part
                set quantity = quantity - %s
                where part_id = %s
            """, (quantity, part["part_id"]))

            cursor.execute("""
                insert into order_part (
                    order_id,
                    part_id,
                    quantity,
                    price
                )
                values (%s, %s, %s, %s)
                returning
                    order_part_id,
                    order_id,
                    part_id,
                    quantity,
                    price
            """, (
                order_id,
                part["part_id"],
                quantity,
                part["price"]
            ))
            new_order_part = cursor.fetchone()

    return new_order_part


@app.delete("/orders/{order_id}/parts/{order_part_id}")
def delete_order_part(order_id: int, order_part_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                select part_id, quantity
                from order_part
                where order_part_id = %s
                and order_id = %s
            """, (order_part_id, order_id))

            order_part = cursor.fetchone()

            if order_part is None:
                raise HTTPException(
                    status_code=404,
                    detail="Order part not found"
                )

            part_id, quantity = order_part

            cursor.execute("""
                update part
                set quantity = quantity + %s
                where part_id = %s
            """, (quantity, part_id))

            cursor.execute("""
                delete from order_part
                where order_part_id = %s
            """, (order_part_id,))

    return {"message": "Order part deleted successfully"}
