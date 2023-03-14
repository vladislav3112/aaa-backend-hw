import logging
import requests
from flask import Flask, request
from models.plate_reader import PlateReader, InvalidImage
import logging
import io
from plate_reader_client import PlateReaderClient
from requests.exceptions import ConnectTimeout, ConnectionError, JSONDecodeError

app = Flask(__name__)
plate_reader = PlateReader.load_from_file('./model_weights/plate_reader_model.pth')


@app.route('/')
def hello():
    return f'<h1 style="color:black;"><center>Hello! Get auto plate number following url: /images/&lt;int:img_id&gt; <a href=/images/9965>example</a></center></h1>'


# <url>:8080/readPlateNumber : body <image bytes>
# {"plate_number": "c180mv ..."}
@app.route('/readPlateNumber', methods=['POST'])
def read_plate_number():
    im = request.get_data()
    im = io.BytesIO(im)

    try:
        res = plate_reader.read_text(im)
    except InvalidImage:
        logging.error('invalid image')
        return {'error': 'invalid image'}, 400

    return {
        'plate_number': res,
    }

@app.route('/images/<int:img_id>')
def read_img_by_id(img_id):
    url = f'http://51.250.83.169:7878/images/{str(img_id)}'
    client = PlateReaderClient(host='http://127.0.0.1:8080')
    if img_id != 10022 and img_id != 9965:
        return 'invalid image id', 400
    try:
        im = requests.get(url, timeout=5)
        res = client.read_plate_number(im)
        print(res)
    except ConnectTimeout:
        return 'Auto plate picture service unavaliable (request timeout)', 416    
    except ConnectionError:
        return 'Auto plate picture service unavaliable', 503
    except JSONDecodeError:
        return 'Auto plate picture not found', 404
    return res

if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname)s] [%(asctime)s] %(message)s',
        level=logging.INFO,
    )

    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=8080, debug=True)
