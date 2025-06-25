from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

httpserver = HttpServer()

#untuk menggunakan threadpool executor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

def ProcessTheClient(connection, address):
    rcv = b""

    try:
        # Step 1: Read until we get all headers (\r\n\r\n)
        while b"\r\n\r\n" not in rcv:
            data = connection.recv(8192)
            if not data:
                break
            rcv += data

        if not rcv:
            connection.close()
            return

        # Step 2: Split headers and body-start
        header_part, _, body_start = rcv.partition(b"\r\n\r\n")
        headers_text = header_part.decode(errors='replace')
        headers = headers_text.split("\r\n")

        # Step 3: Find Content-Length
        content_length = 0
        for h in headers:
            if h.lower().startswith("content-length:"):
                content_length = int(h.split(":", 1)[1].strip())
                break

        # Step 4: Read the rest of the body
        body = body_start
        while len(body) < content_length:
            chunk = connection.recv(8192)
            if not chunk:
                break
            body += chunk

        # Step 5: Keep headers and body separate
        # header_part and body are already defined above
        # Step 6: Pass headers_text and body (bytes) to proses
        hasil = httpserver.proses(headers_text, body)
        hasil = hasil + b"\r\n\r\n"
        connection.sendall(hasil)

    except Exception as e:
        print(f"[!] Error: {e}")

    connection.close()




def Server():
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	my_socket.bind(('0.0.0.0', 8885))
	my_socket.listen(1)

	with ThreadPoolExecutor(20) as executor:
		while True:
				connection, client_address = my_socket.accept()
				#logging.warning("connection from {}".format(client_address))
				p = executor.submit(ProcessTheClient, connection, client_address)
				the_clients.append(p)
				#menampilkan jumlah process yang sedang aktif
				jumlah = ['x' for i in the_clients if i.running()==True]
				print(jumlah)





def main():
	Server()

if __name__=="__main__":
	main()

