package orders

func Validate(id string) string {
	return "valid:" + id
}

func Submit(id string) string {
	return Validate(id)
}
