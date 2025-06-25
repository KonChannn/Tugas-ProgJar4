import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
import json
import shutil
import base64

class HttpServer:
	def __init__(self):
		self.sessions={}
		self.types={}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'

	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.0\r\n")
		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
		for kk in headers:
			resp.append("{}:{}\r\n" . format(kk,headers[kk]))
		resp.append("\r\n")

		response_headers=''
		for i in resp:
			response_headers="{}{}" . format(response_headers,i)
		#menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
		#response harus berupa bytes
		#message body harus diubah dulu menjadi bytes
		if (type(messagebody) is not bytes):
			messagebody = messagebody.encode()

		response = response_headers.encode() + messagebody
		#response adalah bytes
		return response

	def proses(self, headers_text, body):
		# Debug prints
		print("Headers text received:", repr(headers_text))
		print("Body length (bytes):", len(body))
		
		requests = headers_text.split("\r\n")
		print("Split requests:", requests)
		
		baris = requests[0]
		print("Request line:", baris)
		
		# Find the empty line that separates headers from body
		empty_line_index = -1
		for i, line in enumerate(requests):
			if line == '':
				empty_line_index = i
				break
		
		# Split headers
		all_headers = requests[1:empty_line_index] if empty_line_index != -1 else requests[1:]
		print("Headers:", all_headers)

		j = baris.split(" ")
		try:
			method = j[0].upper().strip()
			print("Method:", method)
			
			if (method == 'GET'):
				object_address = j[1].strip()
				return self.http_get(object_address, all_headers)
			if (method == 'POST'):
				object_address = j[1].strip()
				return self.http_post(object_address, all_headers, body)
			if (method == 'DELETE'):
				object_address = j[1].strip()
				return self.http_delete(object_address, all_headers)
			else:
				return self.response(400, 'Bad Request', '', {})
		except IndexError:
			return self.response(400, 'Bad Request', '', {})

	def http_get(self,object_address,headers):
		files = glob('./*')
		thedir='./'
		
		if (object_address == '/'):
			return self.response(200,'OK','Ini Adalah web Server percobaan',dict())

		if (object_address == '/video'):
			return self.response(302,'Found','',dict(location='https://youtu.be/katoxpnTf04'))
			
		if (object_address == '/santai'):
			return self.response(200,'OK','santai saja',dict())
			
		if (object_address == '/list'):
			# List files in current directory
			files_list = []
			for file in os.listdir('.'):
				if os.path.isfile(file):
					files_list.append({
						'name': file,
						'size': os.path.getsize(file),
						'type': os.path.splitext(file)[1]
					})
			response_headers = {'Content-Type': 'application/json'}
			return self.response(200, 'OK', json.dumps(files_list), response_headers)

		object_address=object_address[1:]
		if thedir+object_address not in files:
			return self.response(404,'Not Found','',{})
		fp = open(thedir+object_address,'rb')
		isi = fp.read()
		
		fext = os.path.splitext(thedir+object_address)[1]
		content_type = self.types[fext]
		
		headers={}
		headers['Content-type']=content_type
		
		return self.response(200,'OK',isi,headers)

	def http_post(self, object_address, headers, body):
		"""Handle POST requests for file uploads.
		
		Args:
			object_address: The target path of the POST request
			headers: List of request headers
			body: The request body content
			
		Returns:
			HTTP response with appropriate status code and message
		"""
		# Handle non-upload requests
		if object_address != '/upload':
			return self.response(200, 'OK', f'POST received for {object_address}', {
				'Content-Type': 'text/plain'
			})

		try:
			# Setup upload directory
			thedir = './upload/'
			if not os.path.exists(thedir):
				os.makedirs(thedir)
				print(f"Created directory: {thedir}")

			# Extract filename from multipart data
			filename = None
			file_content = None

			# Get content type and boundary
			content_type = None
			boundary = None
			for header in headers:
				if header.lower().startswith('content-type:'):
					content_type = header.split(':', 1)[1].strip()
					if 'multipart/form-data' in content_type.lower():
						parts = content_type.split('boundary=')
						if len(parts) > 1:
							boundary = parts[1].strip()
							break

			if not boundary:
				return self.response(400, 'Bad Request', 'Missing boundary', {})

			# Process multipart data
			if isinstance(body, str):
				body = body.encode()

			boundary_bytes = b'--' + boundary.encode()
			parts = body.split(boundary_bytes)

			# Extract file information
			for part in parts:
				if b'filename=' in part:
					header_part, _, content_part = part.partition(b'\r\n\r\n')
					headers_str = header_part.decode(errors='ignore')

					# Get filename from headers
					for line in headers_str.splitlines():
						if 'filename=' in line:
							filename = line.split('filename=')[1].strip().strip('"')
							break

					# Get file content
					file_content = content_part
					if file_content.endswith(b'--\r\n'):
						file_content = file_content[:-4]
					elif file_content.endswith(b'--'):
						file_content = file_content[:-2]
					break

			if not filename or not file_content:
				return self.response(400, 'Bad Request', 'No file uploaded', {})

			# Sanitize filename and create full path
			safe_filename = os.path.basename(filename)  # Remove any path traversal
			filepath = os.path.join(thedir, safe_filename)

			# Save file
			with open(filepath, 'wb') as f:
				f.write(file_content)

			# Return success response
			return self.response(201, 'Created', 
				f'File {safe_filename} uploaded successfully ({len(file_content)} bytes)', {
					'Content-Type': 'text/plain'
				})

		except Exception as e:
			print(f"Error in POST handler: {e}")
			return self.response(500, 'Internal Server Error', str(e), {})

	def http_delete(self, object_address, headers):
		"""Handle DELETE requests to remove files"""
		try:
			# Get the filename from headers
			filename = None
			for header in headers:
				if header.lower().startswith('filename:'):
					filename = header.split(':', 1)[1].strip().strip('"')
					break
			
			if not filename:
				return self.response(400, 'Bad Request', 'No filename provided', {})
			
			# Check if file exists in root directory
			if os.path.exists(filename):
				# Get file extension and determine content type
				file_ext = os.path.splitext(filename)[1].lower()
				content_type = self.types.get(file_ext, 'multipart/form-data')
				
				# Delete the file
				os.remove(filename)
				response_headers = {'Content-Type': content_type}
				return self.response(200, 'OK', f'File {filename} deleted successfully', response_headers)
			else:
				return self.response(404, 'Not Found', f'File {filename} not found', {})
		except Exception as e:
			return self.response(500, 'Internal Server Error', str(e), {})

#>>> import os.path
#>>> ext = os.path.splitext('/ak/52.png')

if __name__=="__main__":
	httpserver = HttpServer()
	d = httpserver.proses('GET testing.txt HTTP/1.0', b'testing.txt')
	print(d)
	d = httpserver.proses('GET donalbebek.jpg HTTP/1.0', b'donalbebek.jpg')
	print(d)
	#d = httpserver.http_get('testing2.txt',{})
	#print(d)
#	d = httpserver.http_get('testing.txt')
#	print(d)















