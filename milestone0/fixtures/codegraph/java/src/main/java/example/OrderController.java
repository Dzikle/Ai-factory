package example;

public class OrderController {
    private final OrderService service = new OrderService();

    public String create(String id) {
        return service.submit(id);
    }
}
