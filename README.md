## Homework 3 — Django ORM

The project includes 50 Django ORM queries covering filtering,
relationships, aggregation, annotations, database functions,
bulk updates, query optimization and subqueries.

### Running all queries

```bash
python manage.py queries
```

Queries 40–44 are excluded becuse they modify database data.

### Running a specific query

```bash
python manage.py queries --number 31
```

### Displaying SQL

```bash
python manage.py queries --number 6 --sql
```

### Example output

```text
#31 categories_with_post_count — 1 SQL queries
  Python {'post_count': 16}
  Django {'post_count': 11}
  (8 rows)
```

### Resetting test data

```bash
python manage.py seed --clear
```

The seed cmmand generates realistic creationand update dates
for posts and comments.
