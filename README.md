# ev-fleet-graphql-api

Production-ready Python GraphQL API backend for EV leasing inventory management.

## Stack
- FastAPI
- Strawberry GraphQL
- SQLAlchemy asyncio + asyncpg
- PostgreSQL
- Docker + Docker Compose

## Run with Docker Compose

```bash
docker compose up --build
```

GraphQL endpoint:

- `http://localhost:8000/graphql`

## Example GraphQL operations

### Create EV

```graphql
mutation {
  createEv(
    input: {
      make: "Tesla"
      model: "Model 3"
      batteryCapacityKwh: 75
      rangeMiles: 330
      monthlyLeasePrice: 499.99
      status: AVAILABLE
    }
  ) {
    id
    make
    model
    status
  }
}
```

### Query EVs with filters

```graphql
query {
  evs(make: "Tes", maxPrice: 550, status: "AVAILABLE") {
    id
    make
    model
    monthlyLeasePrice
    status
  }
}
```
