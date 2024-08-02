import cv2
import matplotlib.pyplot as plt
from thermal_cam import Thermal_cam, raw_to_8bit, ktoc
from calibrate import get_merging_function, find_rgb_camera_id, get_shifting_function
from multiprocessing.pool import ThreadPool
import time

class MergeCamera():
    FEVER_THRESHOLD = 37.5 #Degree celsius
    def __init__(self):
        self.thermal_cam = Thermal_cam()
        self.thermal_cam.start()
        self.merge_function = get_merging_function()
        self.rgb_camera = cv2.VideoCapture(find_rgb_camera_id())
        self.face_classifier = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        self.shift_function = get_shifting_function()

    def detectBoundingBox(self, vid):
        gray_image = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
        faces = self.face_classifier.detectMultiScale(gray_image, 1.1, 5, minSize=(40, 40))
        for (x, y, w, h) in faces:
            cv2.rectangle(vid, (x, y), (x + w, y + h), (0, 255, 0), 4)
        return faces


    # Queue allows class to communicate with external process
    def run(self, queue):
        # TODO: temp is off by 5 degree
        try:
            while True:
                # Thermal Camera
                # Need to keep track of the original copy bc cv2 transformation function doesn't work
                # properly without apply raw_to_8bit first
                # But temperature needs the raw values to be correct

                thermal_frame = None
                rgb_frame = None

                thermal_frame = self.thermal_cam.get_thermal_frame()
                _, rgb_frame = self.rgb_camera.read()


                thermal_frame_copy = thermal_frame.copy()
                thermal_frame = self.shift_function(thermal_frame)
                # RGB Camera
                faces = self.detectBoundingBox(rgb_frame)

                # print(thermal_frame.dtype)
                # print(thermal_frame.shape)
                # print(rgb_frame.dtype)
                # print(rgb_frame.shape)
                # exit(1)

                # https://stackoverflow.com/questions/49799057/how-to-draw-a-point-in-an-image-using-given-co-ordinate-with-python-opencv

                # Have to do raw_to_8bit before drawing on thermal frame
                # Calculation using raw thermal_frame value
                temp_reading_position = []
                for (x, y, w, h) in faces:
                    point_x = int(round(x + w/2))
                    point_y = int(round(y + h/2) - 40)
                    if (point_x >= thermal_frame.shape[0] or point_y >= thermal_frame.shape[1]):
                        print(thermal_frame.shape)
                        print(point_x, point_y)
                        continue
                    degree = ktoc(thermal_frame[point_x][point_y])
                    temp_reading_position.append((point_x, point_y, degree))


                # using original thermal_frame_copy to draw description
                thermal_frame_copy = raw_to_8bit(thermal_frame_copy)
                thermal_frame_copy = self.shift_function(thermal_frame_copy)

                for (point_x, point_y, degree) in temp_reading_position:
                    cv2.circle(rgb_frame, (point_x, point_y), radius=5, color=(0,0,255), thickness= - 1)
                    cv2.circle(thermal_frame_copy, (point_x, point_y), radius=5, color=(0,0,255), thickness= - 1)

                    cv2.putText(thermal_frame_copy,"{0:.1f} degC".format(degree), (point_x, point_y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,0,255), 2)
                    cv2.putText(rgb_frame,"{0:.1f} degC".format(degree), (point_x, point_y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,0,255), 2)

                    if degree >= MergeCamera.FEVER_THRESHOLD:                 
                        # TODO: place alert here
                        print("Fever detected")

                merged_frame = self.merge_function(thermal_frame_copy, rgb_frame)

                queue.put({
                    "merged_frame": merged_frame,
                    "faces": faces,
                    "temperature_data": temp_reading_position
                })

                cv2.imshow("merge", merged_frame)
                # cv2.imshow("rgb", rgb_frame)
                # cv2.imshow("thermal", thermal_frame_copy)
                cv2.waitKey(1)
        finally:
            cv2.destroyAllWindows()
            self.thermal_cam.stop()

if __name__ == "__main__":
    merge_camera = MergeCamera()
    merge_camera.run()