def make_post_starting_text(post_type):
    # hardcoding those for now, because it is still unclear 
    # what this feature will look like in a stable state 
    # and will it even exist
    starting_texts = [
        "",
        "Сейчас я работаю в ",
        "Сегодня я узнал, что ",
        "А вот такая задача: ",
        "Мне очень нравится ",
        "Я всегда мечтал сделать ",
        '''https://www.youtube.com/watch?v=
        
        Посмотрите этот ролик, если интересуетесь '''
    ]
    if post_type >= 0 and post_type < len(starting_texts):
        return starting_texts[post_type]
    return ""
