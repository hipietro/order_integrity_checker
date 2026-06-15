from database import create_database, insert_sample_orders
from menu import show_menu


# Program entry point.
# The database is prepared before showing the interactive menu.
create_database()
insert_sample_orders()
show_menu()