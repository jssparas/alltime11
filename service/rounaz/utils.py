def parse_response(response):
	data = response.get("data")
	error = response.get("error")
	return data, error

