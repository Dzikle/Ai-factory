package example;

public class OrderService {
    public String submit(String id) {
        return validate(id);
    }

    public String validate(String id) {
        return "valid:" + id;
    }
}
