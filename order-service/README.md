# Order-Service Endpoints

## Create order

`POST /orders/create/<uuid:userid>`

Creates an order for a user with `userid` and returns

### On Success:

`CODE 200`

```json
{
    "order_id": <uuid:order_id>
}
```

### On Failure

`CODE 500`

```json
{
    "message": "failure"
}
```

## TODO others