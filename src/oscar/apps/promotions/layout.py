def split_by_position(linked_promotions, context):
    """
    Split the list of promotions into separate lists, grouping
    by position, and write these lists to the passed context.
    """
    for linked_promotion in linked_promotions:
        promotion = linked_promotion.content_object
        if not promotion:
            continue
        key = 'promotions_%s' % linked_promotion.position.lower()
        if key not in context:
            context[key] = []
        context[key].append(promotion)
