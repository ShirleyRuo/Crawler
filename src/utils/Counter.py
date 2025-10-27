class Counter:

    def __init__(
            self,
            name : str,
            *,
            total_num : int = 0,
            current_id : int = 0,
            ) -> None:
        self.name = name
        self.total_num = total_num
        self.current_id = current_id
    
    def increment(self) -> None:
        if self.current_id >= self.total_num:
            raise ValueError("计数器错误!")
        self.current_id += 1
    
    def reset(self) -> None:
        self.current_id = 0
