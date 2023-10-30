cd C:\dev\honeycomb
call git pull
call activate honeycomb
call python C:\dev\honeycomb\scripts\wait_for_license_and_server.py
call honeycomb resume
