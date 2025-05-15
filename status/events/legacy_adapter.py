"""
---------------------------------------------------------------
File name:                  legacy_adapter.py
Author:                     Ignorant-lu
Date created:               2025/05/16
Description:                适配器，用于将旧版 EventSystem API 调用桥接到新的 EventManager。
----------------------------------------------------------------

Changed history:            
                            2025/05/16: 初始创建;
                            2025/05/16: 添加对AdvancedEventManager的直接引用;
                            2025/05/16: 添加订阅映射和事件类型枚举的适配;
                            2025/05/16: 添加事件分发和注册处理器的适配;
                            2025/05/16: 添加取消订阅和清空处理器的适配;
----
"""
import logging
from typing import Any, Callable, Dict, Tuple, Optional, List
from enum import Enum

# 直接导入: 这些必须 成功 才能使适配器正常工作。
from status.core.event_system import EventType as OldEventType, Event as OldEvent
from status.events.event_manager import EventManager as AdvancedEventManager
# 修正: EventSubscription 在 event_manager.py 中定义，而不是 event_types.py 中
from status.events.event_manager import EventSubscription as AdvancedEventSubscription

logger = logging.getLogger(__name__)

# 定义 SingletonType 元类
class SingletonType(type):
    _instances: Dict[type, Any] = {}
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class LegacyEventManagerAdapter(metaclass=SingletonType):
    """
    适配器类，将旧版 EventSystem 的API调用桥接到新版 AdvancedEventManager。
    这是一个单例。
    """
    _instance: Optional['LegacyEventManagerAdapter'] = None
    _advanced_event_manager_instance: Optional[AdvancedEventManager] = None # 类级变量，用于存储获取实例后存储实例
    _event_system_instance: Optional[Any] = None # 旧的 _EventSystem 实例
    _registered_handlers: Dict[Tuple[OldEventType, Callable[[OldEvent], None]], AdvancedEventSubscription] = {} # 适配器到原始处理器的映射

    def __init__(self):
        if LegacyEventManagerAdapter._instance is not None:
            # logger.debug("LegacyEventManagerAdapter instance already exists.")
            pass # Allow re-initialization of attributes, but don't raise
        else:
            # logger.debug("Initializing LegacyEventManagerAdapter singleton.")
            LegacyEventManagerAdapter._instance = self
        
        self.logger = logging.getLogger("Status.Events.LegacyAdapter") 
        self.logger.info(f"[LegacyEventManagerAdapter.__init__] Initializing the singleton adapter instance. id(self): {id(self)}")
        # Old event system instance initialization is deferred to first use or set externally
        # self._ensure_old_event_system_initialized() # Avoid auto-loading old system in test environments

    @property
    def advanced_em(self) -> AdvancedEventManager:
        """懒加载获取 AdvancedEventManager 实例"""
        if LegacyEventManagerAdapter._advanced_event_manager_instance is None:
            logger.debug("LegacyAdapter: 第一次调用 advanced_em，获取 AdvancedEventManager 实例...")
            LegacyEventManagerAdapter._advanced_event_manager_instance = AdvancedEventManager() # type: ignore
        if LegacyEventManagerAdapter._advanced_event_manager_instance is None: # Should not happen if get_instance is correct
             logger.critical("LegacyAdapter: AdvancedEventManager() 返回 None!")
             raise RuntimeError("失败获取 AdvancedEventManager 实例。")
        return LegacyEventManagerAdapter._advanced_event_manager_instance

    @classmethod
    def get_instance(cls) -> 'LegacyEventManagerAdapter':
        if cls._instance is None:
            # logger.debug("LegacyAdapter: 创建第一个实例。") # Already logged by __init__ effectively
            cls._instance = cls() # Calls __init__ via SingletonType
        logger.info(f"[LegacyAdapter.get_instance] Returning adapter instance id: {id(cls._instance)}")
        return cls._instance

    def _create_adapted_handler(
        self, 
        original_handler: Callable[[OldEvent], None], 
        original_event_type: OldEventType
    ) -> Callable[[str, Any], None]:
        """创建一个包装处理器，将新事件系统的参数转换为旧的 Event 对象"""
        
        def adapted_handler(event_type_str: str, event_data: Any) -> None:
            self.logger.debug(f"LegacyAdapter._adapted_handler: Received from AdvancedEM. Type_str: '{event_type_str}', Event_data_raw: '{event_data}', Type_of_event_data_raw: '{type(event_data)}'")
            sender: Optional[Any] = None
            actual_data: Optional[Any] = None
            
            if isinstance(event_data, dict):
                sender = event_data.get("_sender_")
                actual_data = event_data.get("_data_")
                self.logger.debug(f"LegacyAdapter._adapted_handler: Extracted from dict. Sender: '{sender}', Actual_data: '{actual_data}', Type_actual_data: '{type(actual_data)}'")
            else:
                actual_data = event_data
                self.logger.debug(f"LegacyAdapter._adapted_handler: Event_data_raw was not dict. Actual_data: '{actual_data}', Type_actual_data: '{type(actual_data)}'")

            legacy_event = OldEvent(original_event_type, sender, actual_data)
            self.logger.debug(f"LegacyAdapter._adapted_handler: Created legacy_event. Type: {legacy_event.type.name}, Data: '{legacy_event.data}', Type_legacy_event.data: '{type(legacy_event.data)}'")
            
            try:
                original_handler(legacy_event)
            except Exception as e:
                handler_name = getattr(original_handler, '__name__', 'unknown_handler')
                logger.error(f"Error in adapted legacy handler '{handler_name}' for {original_event_type.name}: {e}", exc_info=True)

        return adapted_handler

    def register_handler(self, event_type: OldEventType, handler: Callable[[OldEvent], None]) -> None:
        if not isinstance(event_type, Enum): 
            logger.error(f"Adapter: register_handler 期望 Enum 用于 event_type，得到 {type(event_type)}")
            return

        handler_name = getattr(handler, '__name__', 'unknown_handler')
        # logger.debug(f"Adapter: Registering legacy handler '{handler_name}' for {event_type.name}")
        
        handler_key = (event_type, handler)
        if handler_key in self._registered_handlers:
            logger.warning(f"Adapter: Handler '{handler_name}' for {event_type.name} "
                           f"already mapped. Skipping re-registration.")
            return

        adapted_handler_func = self._create_adapted_handler(handler, event_type)
        event_type_str: str = event_type.name
        
        subscription = self.advanced_em.subscribe(event_type_str, adapted_handler_func)
        
        if subscription:
            self._registered_handlers[handler_key] = subscription
            logger.info(f"Adapter: 成功注册 '{handler_name}' 用于 {event_type.name}.")
        else:
            logger.error(f"Adapter: 订阅 '{handler_name}' 失败用于 {event_type.name} (订阅返回 False).")

    def unregister_handler(self, event_type: OldEventType, handler: Callable[[OldEvent], None]) -> bool:
        if not isinstance(event_type, Enum):
            logger.error(f"Adapter: unregister_handler 期望 Enum 用于 event_type，得到 {type(event_type)}")
            return False
        
        handler_name = getattr(handler, '__name__', 'unknown_handler')
        # logger.debug(f"Adapter: Unregistering '{handler_name}' for {event_type.name}")
        handler_key = (event_type, handler)
        
        subscription_to_remove = self._registered_handlers.pop(handler_key, None)
        
        if subscription_to_remove:
            unsubscribed = self.advanced_em.unsubscribe(subscription_to_remove)
            if unsubscribed:
                logger.info(f"Adapter: 成功取消订阅 '{handler_name}' 用于 {event_type.name}.")
                return True
            else:
                logger.warning(f"Adapter: AdvancedEM.unsubscribe 失败用于 '{handler_name}' ({event_type.name}).")
                return False 
        else:
            logger.warning(f"Adapter: 没有映射的订阅用于 '{handler_name}' ({event_type.name}). 不能取消订阅。")
            return False
        
    def dispatch(self, event: OldEvent) -> None:
        if not isinstance(event, OldEvent) or not isinstance(event.type, OldEventType):
            logger.error(f"Adapter: dispatch 期望 OldEvent，得到 {type(event)}")
            return

        # logger.debug(f"Adapter: Dispatching legacy event: {event.type.name}")
        event_type_str: str = event.type.name
        
        data_for_payload = event.data
        # Heuristic check for SystemStatsUpdatedEvent-like objects to avoid circular import
        if hasattr(event.data, 'stats_data') and \
           type(event.data).__name__ == 'SystemStatsUpdatedEvent' and \
           getattr(event.data, 'stats_data') is not None:
            data_for_payload = event.data.stats_data

        adv_event_data: Dict[str, Any] = {
            "_sender_": event.sender,
            "_data_": data_for_payload, # Corrected data extraction
            "_is_legacy_event_": True,
            "_event_type_enum_val_": event.type.value 
        }
        self.advanced_em.emit(event_type_str, adv_event_data)

    def dispatch_event(self, event_type: OldEventType, sender: Any = None, data: Any = None) -> None:
        if not isinstance(event_type, OldEventType):
            logger.error(f"Adapter: dispatch_event 期望 OldEventType，得到 {type(event_type)}")
            return
        # logger.debug(f"Adapter: dispatch_event for {event_type.name}")
        legacy_event = OldEvent(event_type, sender, data)
        self.dispatch(legacy_event)

    def post_event(self, event: OldEvent) -> None:
        """ 
        提供 AdvancedEventManager 的 post_event 兼容性，
        假设它类似于已经创建的事件对象的调度。
        在 AdvancedEventManager 中，post_event 可能用于异步或队列发射。
        这里，我们将它简化为适配器上下文中的调度。
        如果 AdvancedEM.post_event 有特定的异步/队列逻辑，这个适配器会简化它。
        """
        logger.debug(f"Adapter: post_event 调用用于事件类型 {event.type.name if hasattr(event, 'type') else 'UnknownEvent'}. 转发...")
        if not isinstance(event, OldEvent):
            logger.error(f"Adapter: post_event 期望 OldEvent 实例，得到 {type(event)}")
            # Potentially, if post_event in AdvancedEM can take type & data, we could adapt further.
            # For now, assume it takes an event object similar to how _EventSystem did.
            return
        self.dispatch(event) # Forward to existing dispatch logic

    def get_handlers_count(self, event_type: Optional[OldEventType] = None) -> int:
        # logger.warning("Adapter: get_handlers_count only reflects adapter-mapped handlers.")
        if event_type is None:
            return len(self._registered_handlers)
        else:
            if not isinstance(event_type, Enum): return 0
            count = 0
            for (et, _), _ in self._registered_handlers.items():
                if et == event_type:
                    count += 1
            return count

    def clear_handlers(self, event_type: Optional[OldEventType] = None) -> None:
        # logger.warning("Adapter: clear_handlers for adapter-mapped handlers.")
        keys_to_remove: list[Tuple[OldEventType, Callable[[OldEvent], None]]] = []
        if event_type is None:
            keys_to_remove = list(self._registered_handlers.keys())
        else:
            if not isinstance(event_type, Enum): return
            for key_tuple, _ in self._registered_handlers.items():
                if key_tuple[0] == event_type:
                    keys_to_remove.append(key_tuple)
        
        # logger.debug(f"Adapter: clear_handlers removing {len(keys_to_remove)} mapped handlers.")
        for et_key, handler_key_fn in keys_to_remove:
            self.unregister_handler(et_key, handler_key_fn)

    def emit(self, event_type: OldEventType, event_data: Any = None, sender: Optional[Any] = None):
        self.logger.debug(f"LegacyAdapter: emit called with type: {event_type.name if isinstance(event_type, Enum) else event_type}, data type: {type(event_data)}")
        
        payload_data: Any = None
        actual_sender: Optional[Any] = sender # Use the sender passed to emit first

        # Directly inspect the type of event_data
        event_data_type_name = type(event_data).__name__

        if event_data_type_name == "SystemStatsUpdatedEvent":
            # This is when a new SystemStatsUpdatedEvent instance is passed as event_data
            if hasattr(event_data, 'stats_data'):
                payload_data = getattr(event_data, 'stats_data')
                self.logger.debug(f"LegacyAdapter.emit: event_data is SystemStatsUpdatedEvent, using its stats_data.")
            else:
                payload_data = event_data # Fallback, should ideally not happen
                self.logger.warning(f"LegacyAdapter.emit: event_data is SystemStatsUpdatedEvent but no stats_data. Using event_data itself.")
            if hasattr(event_data, 'sender') and actual_sender is None: # Prioritize explicitly passed sender
                actual_sender = event_data.sender

        elif event_data_type_name == "WindowPositionChangedEvent":
            # This is when a new WindowPositionChangedEvent instance is passed as event_data
            payload_data = event_data # The event instance itself is the data for adapted_handler
            self.logger.debug(f"LegacyAdapter.emit: event_data is WindowPositionChangedEvent, using event_data itself as payload.")
            if hasattr(event_data, 'sender') and actual_sender is None:
                actual_sender = event_data.sender
        
        elif isinstance(event_data, OldEvent):
            # This is when an old Event instance is passed
            self.logger.debug(f"LegacyAdapter.emit: event_data is OldEvent. Unwrapping its .data and .sender.")
            old_event_internal_data = event_data.data
            if actual_sender is None: # Prioritize explicitly passed sender
                actual_sender = event_data.sender
            
            # Further unwrap if the OldEvent.data itself is a new event type
            old_event_internal_data_type_name = type(old_event_internal_data).__name__
            if old_event_internal_data_type_name == "SystemStatsUpdatedEvent":
                if hasattr(old_event_internal_data, 'stats_data'):
                    payload_data = getattr(old_event_internal_data, 'stats_data')
                    self.logger.debug(f"LegacyAdapter.emit: OldEvent.data was SystemStatsUpdatedEvent, using its stats_data.")
                else:
                    payload_data = old_event_internal_data # Fallback
            elif old_event_internal_data_type_name == "WindowPositionChangedEvent":
                payload_data = old_event_internal_data # Pass the new event instance
                self.logger.debug(f"LegacyAdapter.emit: OldEvent.data was WindowPositionChangedEvent, using it as payload.")
            else:
                payload_data = old_event_internal_data # Generic data from OldEvent
                self.logger.debug(f"LegacyAdapter.emit: OldEvent.data is generic, using it as payload. Type: {type(payload_data)}")

        else: 
            # event_data is likely raw data (e.g., a dict not wrapped in any event object)
            # or an unknown/unhandled event type instance.
            payload_data = event_data
            self.logger.debug(f"LegacyAdapter.emit: event_data is raw data or unhandled event type. Using event_data as payload. Type: {type(payload_data)}")
            # actual_sender remains what was passed to emit or None (already handled)

        payload_for_new_em: Dict[str, Any] = {
            "_sender_": actual_sender,
            "_data_": payload_data,
            "_is_legacy_event_": True, # Signifies this came via adapter for adapted_handler
            "_event_type_enum_val_": event_type.value if isinstance(event_type, Enum) else None
        }

        if self.advanced_em:
            # Log details before emitting to AdvancedEM
            log_payload_data_repr = str(payload_for_new_em.get('_data_'))[:200] # Avoid overly long logs
            
            self.logger.debug(f"LegacyAdapter: Emitting to AdvancedEM. EventType: '{event_type.name if isinstance(event_type, Enum) else event_type}', "
                              f"Payload's _data_ type: '{type(payload_for_new_em.get('_data_'))}', "
                              f"Payload's _data_ (preview): '{log_payload_data_repr}', "
                              f"Payload's _sender_ type: '{type(payload_for_new_em.get('_sender_'))}'")
            
            # self.logger.debug(f"LegacyAdapter: Raw payload for AdvancedEM.emit: type='{event_type.name if isinstance(event_type, Enum) else event_type}', "
            #                   f"full_payload_dict='{payload_for_new_em}'") # This can be very verbose
            
            self.advanced_em.emit(event_type.name if isinstance(event_type, Enum) else str(event_type), payload_for_new_em)
        else:
            self.logger.warning("LegacyAdapter: Advanced EventManager (advanced_em) is not initialized!")

    def unregister_all_handlers(self, target_handler: Optional[Callable] = None, event_type: Optional[OldEventType] = None):
        keys_to_remove: List[Tuple[OldEventType, Callable[[OldEvent], None]]] = []
        if target_handler is not None:
            # Remove specific handler across all its event types
            for (et, fn), sub in list(self._registered_handlers.items()): # Iterate over a copy
                if fn == target_handler:
                    if event_type is None or et == event_type:
                        if self.advanced_em.unsubscribe(sub):
                            keys_to_remove.append((et, fn))
                            logger.info(f"Adapter: Unsubscribed '{getattr(fn, '__name__', 'handler')}' for {et.name} (specific target).")
                        else:
                            logger.warning(f"Adapter: AdvancedEM.unsubscribe failed for '{getattr(fn, '__name__', 'handler')}' ({et.name}) during unregister_all for target.")
        elif event_type is not None:
            # Remove all handlers for a specific event type
            for (et, fn), sub in list(self._registered_handlers.items()): # Iterate over a copy
                if et == event_type:
                    if self.advanced_em.unsubscribe(sub):
                        keys_to_remove.append((et, fn))
                        logger.info(f"Adapter: Unsubscribed '{getattr(fn, '__name__', 'handler')}' for {et.name} (specific event type).")
                    else:
                        logger.warning(f"Adapter: AdvancedEM.unsubscribe failed for '{getattr(fn, '__name__', 'handler')}' ({et.name}) during unregister_all for event type.")
        else:
            # Remove all handlers for all types
            for (et, fn), sub in list(self._registered_handlers.items()): # Iterate over a copy
                if self.advanced_em.unsubscribe(sub):
                    keys_to_remove.append((et, fn))
                    # logger.debug(f"Adapter: Unsubscribed '{getattr(fn, '__name__', 'handler')}' for {et.name} (all).") # Too verbose
                else:
                    logger.warning(f"Adapter: AdvancedEM.unsubscribe failed for '{getattr(fn, '__name__', 'handler')}' ({et.name}) during unregister_all.")
            logger.info(f"Adapter: Unregistered all ({len(keys_to_remove)}) mapped handlers.")

        for key in keys_to_remove:
            self._registered_handlers.pop(key, None)
        
        if not keys_to_remove and target_handler is None and event_type is None:
            logger.info("Adapter: unregister_all_handlers called, but no handlers were registered through adapter.")

