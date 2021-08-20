import os
import io
import json
import glob
from PIL import Image
from tqdm import tqdm
import base64

if __name__ == "__main__":

    image_format = "jpg"
    image_dir = "../data/images"
    output_path = "../data/images/image_bytes.json"
    
    json_file_path = os.path.join(image_dir, "info.json")
    
    with open(json_file_path, "r") as read_file:
        index_map = json.load(read_file)
    
    image_info = {}
    
    for name, index in tqdm(index_map.items()):
        
        image_paths = glob.glob(os.path.join(image_dir, "{:04d}".format(index), "*.{}".format(image_format)))
        
        images = []
        for image_path in image_paths:
            
            img = Image.open(image_path, mode='r')            
            image_data = io.BytesIO()
            img.save(image_data, format='JPEG')
            image_data = image_data.getvalue()
            image_data = base64.b64encode(image_data).decode("utf-8")
            
            images.append(image_data)
            # from byte to image
            #print(image_data)
            #image = Image.open(io.BytesIO(base64.b64decode(image_data.encode("utf-8"))))
            #image.show()
            #break
        
        image_info[name] = images
        #break
        
    with open(output_path, "w") as write_file:
        json.dump(image_info, write_file)