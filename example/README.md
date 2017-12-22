##Example Project

This example is provided as a convenience feature to allow potential users to try the app straight from the app repo without having to create a Django project.

It can also be used to develop the app in place.

To run this example, follow these instructions:

1. Navigate to the `example` directory
2. Install the requirements for the package:
		
		pip install -r requirements.txt
		
3. Apply the migrations:

		python manage.py migrate quade

4. Run the server

		python manage.py runserver
		
5. Access from the browser at `http://127.0.0.1:8000`
