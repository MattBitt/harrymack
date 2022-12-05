from playhouse.migrate import (
    SqliteDatabase,
    SqliteMigrator,
    CharField,
    IntegerField,
    migrate,
)


my_db = SqliteDatabase("harry_mack.db")
migrator = SqliteMigrator(my_db)


title_field = CharField(default="")
status_field = IntegerField(null=True)

migrate(
    migrator.add_column("some_table", "title", title_field),
    migrator.add_column("some_table", "status", status_field),
    migrator.drop_column("some_table", "old_column"),
)
print("complete")
