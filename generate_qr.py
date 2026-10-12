
import qrcode

gym_url = "http://10.20.88.165:5000/checkin"

qr = qrcode.make(gym_url)

qr.save("gym_entrance_qr.png")

print("Gym entrance QR code created successfully!")
print("Saved as gym_entrance_qr.png")