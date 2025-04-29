from django.shortcuts import render
from django.shortcuts import redirect
from django.http import JsonResponse
import csv
import os
import random
import cv2
from pyzbar.pyzbar import decode
from django.views.decorators.csrf import csrf_exempt

# Configuration
ROOM_NUMBERS = [101, 102, 103, 104, 105]
ROOM_CAPACITY = 30
INPUT_CSV = "D:/candidates.csv"
OUTPUT_CSV = "D:/exam_seating.csv"

room_seat_tracker = {room: [] for room in ROOM_NUMBERS}
allocated_candidates = {}

def load_existing_allocations():
    if not os.path.isfile(OUTPUT_CSV):
        return

    with open(OUTPUT_CSV, mode="r", newline="") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            roll_number = int(row[0])
            name = row[1]
            department = row[2]
            room = int(row[3])
            seat = int(row[4])
            allocated_candidates[roll_number] = (name, department, room, seat)
            if room in room_seat_tracker:
                room_seat_tracker[room].append(seat)

def generate_random_room_seat():
    available_rooms = [room for room, seats in room_seat_tracker.items() if len(seats) < ROOM_CAPACITY]
    
    if not available_rooms:
        return None, None

    room = random.choice(available_rooms)
    available_seats = set(range(1, ROOM_CAPACITY + 1)) - set(room_seat_tracker[room])
    seat = random.choice(list(available_seats))

    room_seat_tracker[room].append(seat)
    return room, seat

def load_candidates():
    candidates = {}
    if not os.path.isfile(INPUT_CSV):
        return candidates
    
    with open(INPUT_CSV, mode="r") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            roll_number = int(row[0])
            name = row[1]
            department = row[2]
            candidates[roll_number] = (name, department)
    return candidates

def save_to_csv(roll_number, name, department, room, seat):
    file_exists = os.path.isfile(OUTPUT_CSV)
    
    with open(OUTPUT_CSV, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Roll Number", "Name", "Department", "Room Number", "Seat Number"])
        writer.writerow([roll_number, name, department, room, seat])

def scan_barcode():
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        for barcode in decode(frame):
            roll_number = barcode.data.decode('utf-8')
            cap.release()
            cv2.destroyAllWindows()
            return int(roll_number)

        cv2.imshow("Barcode Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

@csrf_exempt
def barcode_scan_view(request):
    load_existing_allocations()
    candidates = load_candidates()

    roll_number = scan_barcode()
    if not roll_number:
        return JsonResponse({"error": "No barcode detected."})

    if roll_number in allocated_candidates:
        name, department, room, seat = allocated_candidates[roll_number]
        return JsonResponse({"roll_number": roll_number, "name": name, "department": department, "room": room, "seat": seat, "status": "Already Allocated"})
    elif roll_number in candidates:
        name, department = candidates[roll_number]
        room, seat = generate_random_room_seat()
        if room and seat:
            save_to_csv(roll_number, name, department, room, seat)
            return JsonResponse({"roll_number": roll_number, "name": name, "department": department, "room": room, "seat": seat, "status": "Assigned"})
        else:
            return JsonResponse({"error": "No available room for allocation."})
    else:
        return JsonResponse({"error": "Roll number not found in the candidate list!"})

def home(request):
    return render(request, "index.html")
