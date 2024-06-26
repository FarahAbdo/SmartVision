import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from ultralytics import YOLO
from sort import Sort
from yolo_segmentation import YOLOSegmentation
from streamlit_webrtc import webrtc_streamer
import ultralytics
import filterpy


# Function definitions (same as in YOLOv8_all.py)
def detect_objects(webcam_img, model, tracker):
    results = model(np.array(webcam_img))
    result = results[0]
    bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
    classes = np.array(result.boxes.cls.cpu(), dtype="int")
    confs = np.array(result.boxes.conf.cpu(), dtype="int")

    dets_rgb = []
    for xy, cls, conf in zip(bboxes, classes, confs):
        if cls == 0:
            (x1, y1, x2, y2) = xy
            dets_rgb.append([x1, y1, x2, y2, conf])
    dets_rgb = np.array(dets_rgb)
    boxes_ids = tracker.update(dets_rgb)
    draw = ImageDraw.Draw(webcam_img)
    for box_id in boxes_ids:
        x, y, x2, y2, id = map(int, box_id)
        draw.rectangle([x, y, x2, y2], outline="green", width=2)
        draw.text((x, y - 10), f"ID: {id}", fill="green")
    return webcam_img

def seg_objects(webcam_img, model, alpha=0.4):
    overlay = webcam_img.copy()
    bboxes, classes, segmentations, scores, names = model.detect(np.array(webcam_img))
    draw = ImageDraw.Draw(webcam_img)
    overlay_draw = ImageDraw.Draw(overlay)
    for bbox, class_id, seg, score in zip(bboxes, classes, segmentations, scores):
        (x, y, x2, y2) = bbox
        if class_id == 0:
            draw.rectangle([x, y, x2, y2], outline="blue", width=2)
            overlay_draw.polygon(seg, outline="red", fill=(255, 0, 0, int(255 * alpha)))
            draw.text((x, y - 5), names[class_id], fill="red")
    webcam_img = Image.blend(webcam_img, overlay, alpha=alpha)
    return webcam_img

def pos_objects(webcam_img, model, kpt_color, skeleton, limb_color):
    results = model(np.array(webcam_img))
    result = results[0]
    keypoints = result.keypoints.xy.cpu().numpy()
    draw = ImageDraw.Draw(webcam_img)
    for kpt in reversed(keypoints):
        for i, k in enumerate(kpt):
            color_k = tuple(map(int, kpt_color[i]))
            x_coord, y_coord = k[0], k[1]
            if x_coord % webcam_img.width != 0 and y_coord % webcam_img.height != 0:
                if len(k) == 3:
                    conf = k[2]
                    if conf < 0.5:
                        continue
                draw.ellipse([x_coord - 5, y_coord - 5, x_coord + 5, y_coord + 5], fill=color_k)
        if kpt is not None:
            if kpt.shape[0] != 0:
                for i, sk in enumerate(skeleton):
                    pos1 = (int(kpt[(sk[0] - 1), 0]), int(kpt[(sk[0] - 1), 1]))
                    pos2 = (int(kpt[(sk[1] - 1), 0]), int(kpt[(sk[1] - 1), 1]))
                    if kpt.shape[-1] == 3:
                        conf1 = kpt[(sk[0] - 1), 2]
                        conf2 = kpt[(sk[1] - 1), 2]
                        if conf1 < 0.5 or conf2 < 0.5:
                            continue
                    draw.line([pos1, pos2], fill=tuple(map(int, limb_color[i])), width=2)
    return webcam_img

def run_inference(mode):
    if mode == 'Object Detection':
        model = YOLO("yolov8n.pt")
        tracker = Sort()
        process_frame = lambda frame: detect_objects(frame, model, tracker)
    elif mode == 'Object Segmentation':
        model = YOLOSegmentation("yolov8n-seg.pt")
        process_frame = lambda frame: seg_objects(frame, model)
    elif mode == 'Pose Estimation':
        palette = np.array([[255, 128, 0], [255, 153, 51], [255, 178, 102], [230, 230, 0], [255, 153, 255],
                            [153, 204, 255], [255, 102, 255], [255, 51, 255], [102, 178, 255], [51, 153, 255],
                            [255, 153, 153], [255, 102, 102], [255, 51, 51], [153, 255, 153], [102, 255, 102],
                            [51, 255, 51], [0, 255, 0], [0, 0, 255], [255, 0, 0], [255, 255, 255]],
                           dtype=np.uint8)
        skeleton = [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12], [7, 13], [6, 7], [6, 8], [7, 9],
                    [8, 10], [9, 11], [2, 3], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]]
        kpt_color = palette[[16, 16, 16, 16, 16, 0, 0, 0, 0, 0, 0, 9, 9, 9, 9, 9, 9]]
        limb_color = palette[[9, 9, 9, 9, 7, 7, 7, 0, 0, 0, 0, 0, 16, 16, 16, 16, 16, 16, 16]]
        model = YOLO("yolov8n-pose.pt")
        process_frame = lambda frame: pos_objects(frame, model, kpt_color, skeleton, limb_color)

    cap = cv2.VideoCapture(0)
    stop = st.button("Stop Camera")

    stframe = st.empty()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            st.write("Error: Could not read frame")
            break

        frame = Image.fromarray(frame)
        frame = process_frame(frame)
        stframe.image(np.array(frame), channels="RGB")

        if stop:
            break

    cap.release()

# Streamlit interface
st.title("Smart Vision (YOLOv8 Inference)")
st.sidebar.markdown("### Developed by Farah Abdou")
mode = st.selectbox("Choose a mode:", ["Object Detection", "Object Segmentation", "Pose Estimation"])

if st.button("Start Camera"):
    run_inference(mode)



# import streamlit as st
# import cv2
# import numpy as np
# from ultralytics import YOLO
# from sort import Sort
# from yolo_segmentation import YOLOSegmentation
# from streamlit_webrtc import webrtc_streamer
# import ultralytics
# import filterpy
# # Function definitions (same as in YOLOv8_all.py)
# def detect_objects(webcam_img, model, tracker):
#     results = model(webcam_img)
#     result = results[0]
#     bboxes = np.array(result.boxes.xyxy.cpu(), dtype="int")
#     classes = np.array(result.boxes.cls.cpu(), dtype="int")
#     confs = np.array(result.boxes.conf.cpu(), dtype="int")

#     dets_rgb = []
#     for xy, cls, conf in zip(bboxes, classes, confs):
#         if cls == 0:
#             (x1, y1, x2, y2) = xy
#             dets_rgb.append([x1, y1, x2, y2, conf])
#     dets_rgb = np.array(dets_rgb)
#     boxes_ids = tracker.update(dets_rgb)
#     for box_id in boxes_ids:
#         x, y, x2, y2, id = map(int, box_id)
#         cv2.putText(webcam_img, f"ID: {id}", (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 3)
#         cv2.rectangle(webcam_img, (x, y), (x2, y2), (0, 255, 0), 2)
#     return webcam_img

# def seg_objects(webcam_img, model, alpha=0.4):
#     seg_rgb = []
#     overlay = webcam_img.copy()
#     bboxes, classes, segmentations, scores, names = model.detect(webcam_img)
#     for bbox, class_id, seg, score in zip(bboxes, classes, segmentations, scores):
#         (x, y, x2, y2) = bbox
#         if class_id == 0:
#             cv2.rectangle(webcam_img, (x, y), (x2, y2), (255, 0, 0), 2)
#             cv2.polylines(webcam_img, [seg], True, (0, 0, 255), 4)
#             cv2.fillPoly(overlay, [seg], (0, 0, 255))
#             cv2.putText(webcam_img, names[class_id], (x, y - 5), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 3)
#             seg_rgb.append(seg)
#     webcam_img = cv2.addWeighted(overlay, alpha, webcam_img, 1 - alpha, 0)
#     return webcam_img

# def pos_objects(webcam_img, model, kpt_color, skeleton, limb_color):
#     results = model(webcam_img)
#     result = results[0]
#     keypoints = result.keypoints.xy.cpu().numpy()
#     for kpt in reversed(keypoints):
#         for i, k in enumerate(kpt):
#             color_k = [int(x) for x in kpt_color[i]]
#             x_coord, y_coord = k[0], k[1]
#             if x_coord % webcam_img.shape[1] != 0 and y_coord % webcam_img.shape[0] != 0:
#                 if len(k) == 3:
#                     conf = k[2]
#                     if conf < 0.5:
#                         continue
#                 cv2.circle(webcam_img, (int(x_coord), int(y_coord)), 5, color_k, -1, lineType=cv2.LINE_AA)
#         if kpt is not None:
#             if kpt.shape[0] != 0:
#                 for i, sk in enumerate(skeleton):
#                     pos1 = (int(kpt[(sk[0] - 1), 0]), int(kpt[(sk[0] - 1), 1]))
#                     pos2 = (int(kpt[(sk[1] - 1), 0]), int(kpt[(sk[1] - 1), 1]))
#                     if kpt.shape[-1] == 3:
#                         conf1 = kpt[(sk[0] - 1), 2]
#                         conf2 = kpt[(sk[1] - 1), 2]
#                         if conf1 < 0.5 or conf2 < 0.5:
#                             continue
#                     if pos1[0] % webcam_img.shape[1] == 0 or pos1[1] % webcam_img.shape[0] == 0 or pos1[0] < 0 or pos1[1] < 0:
#                         continue
#                     if pos2[0] % webcam_img.shape[1] == 0 or pos2[1] % webcam_img.shape[0] == 0 or pos2[0] < 0 or pos2[1] < 0:
#                         continue
#                     cv2.line(webcam_img,
#                              pos1, pos2,
#                              [int(x) for x in limb_color[i]],
#                              thickness=2, lineType=cv2.LINE_AA)
#     return webcam_img

# def run_inference(mode):
#     if mode == 'Object Detection':
#         model = YOLO("yolov8n.pt")
#         tracker = Sort()
#         process_frame = lambda frame: detect_objects(frame, model, tracker)
#     elif mode == 'Object Segmentation':
#         model = YOLOSegmentation("yolov8n-seg.pt")
#         process_frame = lambda frame: seg_objects(frame, model)
#     elif mode == 'Pose Estimation':
#         palette = np.array([[255, 128, 0], [255, 153, 51], [255, 178, 102], [230, 230, 0], [255, 153, 255],
#                             [153, 204, 255], [255, 102, 255], [255, 51, 255], [102, 178, 255], [51, 153, 255],
#                             [255, 153, 153], [255, 102, 102], [255, 51, 51], [153, 255, 153], [102, 255, 102],
#                             [51, 255, 51], [0, 255, 0], [0, 0, 255], [255, 0, 0], [255, 255, 255]],
#                            dtype=np.uint8)
#         skeleton = [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12], [7, 13], [6, 7], [6, 8], [7, 9],
#                     [8, 10], [9, 11], [2, 3], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]]
#         kpt_color = palette[[16, 16, 16, 16, 16, 0, 0, 0, 0, 0, 0, 9, 9, 9, 9, 9, 9]]
#         limb_color = palette[[9, 9, 9, 9, 7, 7, 7, 0, 0, 0, 0, 0, 16, 16, 16, 16, 16, 16, 16]]
#         model = YOLO("yolov8n-pose.pt")
#         process_frame = lambda frame: pos_objects(frame, model, kpt_color, skeleton, limb_color)

#     cap = cv2.VideoCapture(0)
#     stop = st.button("Stop Camera")

#     stframe = st.empty()

#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             st.write("Error: Could not read frame")
#             break

#         frame = process_frame(frame)
#         stframe.image(frame, channels="BGR")

#         if stop:
#             break

#     cap.release()

# # Streamlit interface
# st.title("Smart Vision (YOLOv8 Inference)")
# st.sidebar.markdown("### Developed by Farah Abdou")
# mode = st.selectbox("Choose a mode:", ["Object Detection", "Object Segmentation", "Pose Estimation"])

# if st.button("Start Camera"):
#     run_inference(mode)



