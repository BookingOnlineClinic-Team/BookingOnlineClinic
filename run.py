"""
Entrypoint chạy app. index.py chỉ khai báo route nên KHÔNG đặt app.run() trong
đó — chạy `python run.py` để start server dev.
"""
from bookingonline import app

if __name__ == "__main__":
    app.run(debug=True)
