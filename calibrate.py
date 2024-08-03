from thermal_cam import Thermal_cam
import cv2
import matplotlib.pyplot as plt
from cv2_enumerate_cameras import enumerate_cameras
import dill as pickle
import numpy as np
from thermal_cam import raw_to_8bit, ktoc, display_temperature

def find_rgb_camera_id():
    camera_ids = []
    for camera_info in enumerate_cameras():
        if (camera_info.name == "Intel(R) RealSense(TM) Depth Camera 435 with RGB Module RGB"):
            camera_ids.append(camera_info.index)

        # print(f'{camera_info.index}: {camera_info.name}')
    return sorted(camera_ids)[0]



def calibrate():
    cv2.namedWindow("rgb")
    cv2.namedWindow("thermal")

    get_rgb_frame = cv2.VideoCapture(find_rgb_camera_id())
    rgb_mouse_pos = []
    def rgb_mouse_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print("rgb:", (x,y))
            rgb_mouse_pos.append((x,y))
    cv2.setMouseCallback("rgb", rgb_mouse_event)

    thermal_mouse_pos = []
    def thermal_mouse_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print("thermal:", (x,y))
            thermal_mouse_pos.append((x,y))
    cv2.setMouseCallback("thermal", thermal_mouse_event)

    try:
        thermal_cam = Thermal_cam()
        thermal_cam.start()
        while True:
            result, video_frame1 = get_rgb_frame.read()
            video_frame2 = thermal_cam.get_thermal_frame()
            cv2.imshow("rgb", video_frame1)
            cv2.imshow("thermal", video_frame2)
            cv2.waitKey(1)
        cv2.destroyAllWindows()
    finally:
        thermal_cam.stop()
        get_rgb_frame.release()
        print(rgb_mouse_pos)
        print(thermal_mouse_pos)
        with open("rgb_points1", "wb") as fp:
            pickle.dump(rgb_mouse_pos, fp)

        with open("thermal_points1", "wb") as fp:
            pickle.dump(thermal_mouse_pos, fp)


# Overlay src_img to destination image
def overlay(src_img, dest_img):
    return cv2.addWeighted(dest_img, 0.4, src_img, 0.5, 0)


def get_distance_vectoc(point1, point2):
    return (point1[0] - point2[0], point1[1], point2[1])

def detectBoundingBox(vid):
    face_classifier = cv2.CascadeClassifier("./haarcascade_frontalface_default.xml")
    vid2 = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(vid2, 1.1, 5, minSize=(40, 40))
    for (x, y, w, h) in faces:
        cv2.rectangle(vid, (x, y), (x + w, y + h), (0, 255, 0), 4)
    return faces

def caculate_offset():
    OFFSET_X = 0
    OFFSET_Y = -325

    rgb_mouse_pos = []
    with open("rgb_points1", "rb") as fp:
        rgb_mouse_pos = pickle.load(fp)
    
    thermal_mouse_pos = []
    with open("thermal_points1", "rb") as fp:
        thermal_mouse_pos = pickle.load(fp)

    print(rgb_mouse_pos)
    print(thermal_mouse_pos)
    distance_vector = []
    for i in range(len(rgb_mouse_pos)):
        distance_vector.append(get_distance_vectoc(rgb_mouse_pos[i], thermal_mouse_pos[i]))

    average_x = sum([df[0] for df in distance_vector])/len(distance_vector) + OFFSET_X
    # + is down
    average_y = sum([df[2] for df in distance_vector])/len(distance_vector) + OFFSET_Y
    trans_matrix = np.float32([[1, 0, average_x], [0, 1, average_y]])

    get_rgb_frame = cv2.VideoCapture(find_rgb_camera_id())
    try:
        thermal_cam = Thermal_cam()
        thermal_cam.start()
        while True:
            result, video_frame1 = get_rgb_frame.read()
            video_frame2 = thermal_cam.get_thermal_frame()

            detectBoundingBox(video_frame1)

            # Need to be in this order
            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(video_frame2)
            img3 = raw_to_8bit(video_frame2)
            img3 = cv2.warpAffine(img3, trans_matrix, (video_frame1.shape[1], video_frame1.shape[0]))

            display_temperature(img3, minVal, minLoc, (255, 0, 0))
            display_temperature(img3, maxVal, maxLoc, (0, 0, 255))

            cv2.imshow("merged", overlay(img3, video_frame1))
            cv2.waitKey(1)
    finally:
        thermal_cam.stop()
        get_rgb_frame.release()
        cv2.destroyAllWindows()
        return trans_matrix



def get_merging_function():
    with open("trans_matrix", "rb") as fp:
        trans_matrix = pickle.load(fp)
        def merge_image(src_image, onto_image):
            # shifted_src_image = cv2.warpAffine(src_image, trans_matrix, (onto_image.shape[1], onto_image.shape[0]))
            return overlay(src_image, onto_image) 
        return merge_image

def get_shifting_function():
    with open("trans_matrix", "rb") as fp:
        trans_matrix = pickle.load(fp)
        def shift_image(src_image):
            shifted_src_image = cv2.warpAffine(src_image, trans_matrix, (src_image.shape[0], src_image.shape[1]))
            return shifted_src_image
        return shift_image

if __name__ == "__main__":
    trans_matrix = caculate_offset()
    # with open("trans_matrix", "wb") as fp:
    #     pickle.dump(trans_matrix, fp)