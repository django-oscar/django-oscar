Feature: Wishlists

    Wishlists provide customers with the ability to keep a list of products that
    they can share with other users.

    Scenario: Create a new wishlist
        Given an authenticated user
        And they visit a product detail page
        When they click "Add to wishlist"
        Then a wishlist is created
        And the product is in the wishlist
