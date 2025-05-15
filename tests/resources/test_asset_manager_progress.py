import pytest
from unittest.mock import Mock, patch, call
import uuid

from status.resources.asset_manager import AssetManager
from status.resources.resource_loader import ResourceLoader # 假设AssetManager依赖它
from status.core.events import EventManager, EventType # 假设事件在此定义或通过此管理器访问
# 占位：稍后会从 status.events.event_types 导入具体的事件类
# from status.events.event_types import ResourceLoadingBatchStartEvent, ResourceLoadingProgressEvent, ResourceLoadingBatchCompleteEvent
from status.core.errors import AssetLoadError # 假设的错误类型

# 使用真实的事件类型定义替换模拟类
from status.events.event_types import ResourceEventType, ResourceLoadingBatchStartEvent, ResourceLoadingProgressEvent, ResourceLoadingBatchCompleteEvent


@pytest.fixture
def mock_event_manager():
    """提供一个EventManager的模拟实例。"""
    manager = Mock(spec=EventManager)
    manager.emit = Mock()
    return manager

@pytest.fixture
def mock_resource_loader(): # This fixture might not be directly used if AssetManager instantiates its own
    """提供一个ResourceLoader的模拟实例。"""
    loader = Mock(spec=ResourceLoader)
    loader.load_resource = Mock()
    return loader

@pytest.fixture
def asset_manager_instance(monkeypatch): # Simplified fixture
    """创建一个AssetManager实例，并注入模拟的EventManager。"""
    # Relies on global cleanup_asset_manager_singleton from conftest.py for instance reset.
    am = AssetManager.get_instance() # This will call the actual __init__

    # AssetManager.__init__ creates its own EventManager instance.
    # We need to mock the EventManager class if we want to intercept calls globally before AM uses it,
    # or mock the instance on 'am' after it's created.
    # For these tests, mocking the instance on 'am' is fine.
    mock_event_manager_instance = Mock(spec=EventManager)
    mock_event_manager_instance.emit = Mock() # Ensure the mock has an emit method
    monkeypatch.setattr(am, '_event_manager', mock_event_manager_instance)

    # AssetManager.__init__ also creates its own ResourceLoader instance (am.loader).
    # The tests for batch loading primarily mock `am.load_asset` itself, so direct
    # interaction with `am.loader` might not need extensive mocking in this fixture,
    # as long as `am.load_asset` is properly patched in the tests.
    # However, ensure `am.loader` exists if any part of AM not being tested relies on it.
    if not hasattr(am, 'loader') or am.loader is None:
        # This case should ideally not happen if __init__ runs correctly.
        am.loader = Mock(spec=ResourceLoader) 

    # Call initialize to complete setup, self.logger is used here.
    am.initialize(base_path="dummy_base_for_progress_tests") 
    am.clear_all_caches() # Ensure clean state for caches
    
    return am


class TestAssetManagerProgress:
    """测试AssetManager的资源加载进度监控功能。"""

    def test_load_assets_batch_success_events(self, asset_manager_instance: AssetManager, mock_resource_loader: Mock):
        """
        测试成功加载一批资源时，是否正确发布了 Start, Progress 和 Complete 事件。
        """
        mock_event_manager = asset_manager_instance._event_manager # Get the patched mock
        asset_paths = ["path/to/asset1.png", "path/to/asset2.json", "path/to/asset3.txt"]
        batch_description = "Test Batch Loading"
        
        # 模拟 ResourceLoader.load_resource 总是成功返回模拟资源内容
        mock_resource_loader.load_resource.side_effect = lambda path, **kwargs: f"content_of_{path}"
        
        # 模拟 AssetManager._load_single_asset_from_loader 行为
        # 这个方法内部会调用 loader.load_resource
        # 我们假设它成功加载并返回一个模拟的资源对象或内容
        def mock_load_single_asset(path, resource_type=None, use_cache=True, **kwargs):
            # 实际的 AssetManager.load_asset 会更复杂，这里简化模拟其核心加载部分
            # 它会调用 self.loader.load_resource
            # 这里我们直接返回，因为 mock_resource_loader.load_resource 已经被 side_effect 模拟
            return mock_resource_loader.load_resource(path, resource_type=resource_type, use_cache=use_cache, **kwargs)

        # 使用 patch 来模拟 _load_single_asset_from_loader，因为它在 AssetManager 内部被调用
        # 注意：如果 load_assets_batch 直接调用 load_asset，那么应该模拟 load_asset
        # 根据设计，load_assets_batch 会调用 AssetManager 自身的 load_asset 方法
        with patch.object(asset_manager_instance, 'load_asset', side_effect=mock_load_single_asset) as mock_load_asset_method:
            batch_id = asset_manager_instance.load_assets_batch(asset_paths, batch_description)

        assert batch_id is not None
        assert isinstance(batch_id, str)

        # 验证事件发布
        assert mock_event_manager.emit.call_count == len(asset_paths) + 2 # Start, N Progress, Complete

        # 1. 验证 ResourceLoadingBatchStartEvent
        start_event_call = mock_event_manager.emit.call_args_list[0]
        # emit 的第一个参数是 event_type (str)，第二个是 event_data (事件对象实例)
        assert start_event_call[0][0] == ResourceEventType.BATCH_LOADING_START.value # 验证事件类型字符串
        start_event_args = start_event_call[0][1] # 事件对象实例
        
        # assert start_event_args.type == ResourceEventType.BATCH_LOADING_START.value # 事件对象内部也应有 type 属性
        # 检查事件对象本身的 TYPE 类属性是否与传递的 event_type 字符串匹配
        assert start_event_args.TYPE == ResourceEventType.BATCH_LOADING_START.value

        assert start_event_args.batch_id == batch_id
        assert start_event_args.total_resources == len(asset_paths)
        assert start_event_args.description == batch_description

        # 2. 验证 ResourceLoadingProgressEvent (为每个资源发布一次)
        for i, path in enumerate(asset_paths):
            progress_event_call = mock_event_manager.emit.call_args_list[i + 1]
            assert progress_event_call[0][0] == ResourceEventType.BATCH_LOADING_PROGRESS.value # 验证事件类型字符串
            progress_event_args = progress_event_call[0][1] # 事件对象实例
            
            # assert progress_event_args.type == ResourceEventType.BATCH_LOADING_PROGRESS.value
            assert progress_event_args.TYPE == ResourceEventType.BATCH_LOADING_PROGRESS.value
            assert progress_event_args.batch_id == batch_id
            assert progress_event_args.resource_path == path
            assert progress_event_args.loaded_count == i + 1
            assert progress_event_args.total_resources == len(asset_paths)
            expected_progress = (i + 1) / len(asset_paths)
            assert abs(progress_event_args.progress_percent - expected_progress) < 1e-9

        # 3. 验证 ResourceLoadingBatchCompleteEvent
        complete_event_call = mock_event_manager.emit.call_args_list[-1]
        assert complete_event_call[0][0] == ResourceEventType.BATCH_LOADING_COMPLETE.value # 验证事件类型字符串
        complete_event_args = complete_event_call[0][1] # 事件对象实例

        # assert complete_event_args.type == ResourceEventType.BATCH_LOADING_COMPLETE.value
        assert complete_event_args.TYPE == ResourceEventType.BATCH_LOADING_COMPLETE.value
        assert complete_event_args.batch_id == batch_id
        assert complete_event_args.loaded_count == len(asset_paths)
        assert complete_event_args.total_resources == len(asset_paths)
        assert complete_event_args.succeeded is True
        assert len(complete_event_args.errors) == 0
        
        # 验证 AssetManager.load_asset 被正确调用
        assert mock_load_asset_method.call_count == len(asset_paths)
        for i, path in enumerate(asset_paths):
            # AssetManager.load_asset 期望的调用参数可能更复杂，这里仅作基本检查
            # 例如，它可能会根据文件扩展名推断 resource_type
            # 在这个测试中，我们主要关注 load_assets_batch 的事件发布逻辑
            mock_load_asset_method.assert_any_call(path)


    def test_load_assets_batch_partial_failure_events(self, asset_manager_instance: AssetManager, mock_resource_loader: Mock):
        """
        测试批量加载中部分资源失败时，事件是否正确发布，特别是 Complete 事件的 succeeded 和 errors 字段。
        """
        mock_event_manager = asset_manager_instance._event_manager # Get the patched mock
        asset_paths = ["path/to/asset_ok.png", "path/to/asset_fail.json", "path/to/asset_ok_too.txt"]
        fail_path = "path/to/asset_fail.json"
        batch_description = "Test Batch Partial Failure"
        error_message = "Failed to load due to reasons."

        # 模拟 ResourceLoader.load_resource
        def mock_load_resource_with_failure(path, **kwargs):
            if path == fail_path:
                raise AssetLoadError(error_message) # AssetLoadError 或其他定义好的异常
            return f"content_of_{path}"
        mock_resource_loader.load_resource.side_effect = mock_load_resource_with_failure

        # 模拟 AssetManager.load_asset
        def mock_load_asset_with_failure(path, **kwargs):
            if path == fail_path:
                raise AssetLoadError(f"AssetManager: {error_message}") # AssetManager 可能包装异常
            return mock_resource_loader.load_resource(path, **kwargs) # 成功路径

        with patch.object(asset_manager_instance, 'load_asset', side_effect=mock_load_asset_with_failure) as mock_load_asset_method:
            batch_id = asset_manager_instance.load_assets_batch(asset_paths, batch_description)

        assert batch_id is not None

        # 验证事件发布总数: Start, 3 Progress, Complete = 5 events
        assert mock_event_manager.emit.call_count == len(asset_paths) + 2

        # 1. 验证 StartEvent (与成功案例类似，此处略去详细属性检查，假设其正确性已由前一个测试保证)
        start_event_call = mock_event_manager.emit.call_args_list[0]
        assert start_event_call[0][0] == ResourceEventType.BATCH_LOADING_START.value
        start_event_args = start_event_call[0][1]
        assert start_event_args.batch_id == batch_id
        assert start_event_args.total_resources == len(asset_paths)

        # 2. 验证 ProgressEvents (为每个资源都发布一次，无论成功失败)
        loaded_count_tracker = 0
        for i, path in enumerate(asset_paths):
            progress_event_call = mock_event_manager.emit.call_args_list[i + 1]
            assert progress_event_call[0][0] == ResourceEventType.BATCH_LOADING_PROGRESS.value
            progress_event_args = progress_event_call[0][1]
            
            loaded_count_tracker +=1 # 即使失败，也算作已尝试加载
            assert progress_event_args.batch_id == batch_id
            assert progress_event_args.resource_path == path
            assert progress_event_args.loaded_count == loaded_count_tracker
            assert progress_event_args.total_resources == len(asset_paths)

        # 3. 验证 CompleteEvent
        complete_event_call = mock_event_manager.emit.call_args_list[-1]
        assert complete_event_call[0][0] == ResourceEventType.BATCH_LOADING_COMPLETE.value
        complete_event_args = complete_event_call[0][1]

        assert complete_event_args.batch_id == batch_id
        # loaded_count 应该是尝试加载的总数
        assert complete_event_args.loaded_count == len(asset_paths)
        assert complete_event_args.total_resources == len(asset_paths)
        assert complete_event_args.succeeded is False
        assert len(complete_event_args.errors) == 1
        assert complete_event_args.errors[0][0] == fail_path
        # 检查错误消息是否包含原始错误信息的一部分
        assert error_message in complete_event_args.errors[0][1] 

        # 验证 AssetManager.load_asset 被正确调用次数
        assert mock_load_asset_method.call_count == len(asset_paths)

    def test_load_assets_batch_empty_list(self, asset_manager_instance: AssetManager, mock_resource_loader: Mock):
        """
        测试当传入一个空资源列表时，是否正确发布 Start 和 Complete 事件，且没有 Progress 事件。
        """
        mock_event_manager = asset_manager_instance._event_manager # Get the patched mock
        asset_paths = []
        batch_description = "Test Empty Batch"

        with patch.object(asset_manager_instance, 'load_asset') as mock_load_asset_method:
            batch_id = asset_manager_instance.load_assets_batch(asset_paths, batch_description)

        assert batch_id is not None

        # 验证事件发布总数: Start, Complete = 2 events
        assert mock_event_manager.emit.call_count == 2

        # 1. 验证 StartEvent
        start_event_call = mock_event_manager.emit.call_args_list[0]
        assert start_event_call[0][0] == ResourceEventType.BATCH_LOADING_START.value
        start_event_args = start_event_call[0][1]
        assert start_event_args.batch_id == batch_id
        assert start_event_args.total_resources == 0
        assert start_event_args.description == batch_description

        # 2. 验证 CompleteEvent
        complete_event_call = mock_event_manager.emit.call_args_list[1]
        assert complete_event_call[0][0] == ResourceEventType.BATCH_LOADING_COMPLETE.value
        complete_event_args = complete_event_call[0][1]

        assert complete_event_args.batch_id == batch_id
        assert complete_event_args.loaded_count == 0
        assert complete_event_args.total_resources == 0
        assert complete_event_args.succeeded is True
        assert len(complete_event_args.errors) == 0
        
        # 确保 load_asset 没有被调用
        mock_load_asset_method.assert_not_called()

    def test_load_assets_batch_all_fail(self, asset_manager_instance: AssetManager, mock_resource_loader: Mock):
        """
        测试批量加载中所有资源都失败时，事件是否正确发布。
        """
        mock_event_manager = asset_manager_instance._event_manager # Get the patched mock
        asset_paths = ["path/to/asset1.png", "path/to/asset2.json"]
        batch_description = "Test Batch All Failures"
        error_message_template = "Failed to load asset at {path}"

        # 模拟 ResourceLoader.load_resource 总是失败
        def mock_load_resource_always_fail(path, **kwargs):
            raise AssetLoadError(error_message_template.format(path=path))
        mock_resource_loader.load_resource.side_effect = mock_load_resource_always_fail
        
        # 模拟 AssetManager.load_asset 总是失败
        def mock_load_asset_always_fail(path, **kwargs):
            raise AssetLoadError(f"AssetManager: {error_message_template.format(path=path)}")
        
        with patch.object(asset_manager_instance, 'load_asset', side_effect=mock_load_asset_always_fail) as mock_load_asset_method:
            batch_id = asset_manager_instance.load_assets_batch(asset_paths, batch_description)

        assert batch_id is not None

        # 验证事件发布总数: Start, 2 Progress, Complete = 4 events
        assert mock_event_manager.emit.call_count == len(asset_paths) + 2

        # 1. 验证 StartEvent
        start_event_call = mock_event_manager.emit.call_args_list[0]
        assert start_event_call[0][0] == ResourceEventType.BATCH_LOADING_START.value
        start_event_args = start_event_call[0][1]
        assert start_event_args.batch_id == batch_id
        assert start_event_args.total_resources == len(asset_paths)

        # 2. 验证 ProgressEvents (为每个资源都发布一次)
        loaded_count_tracker = 0
        for i, path in enumerate(asset_paths):
            progress_event_call = mock_event_manager.emit.call_args_list[i + 1]
            assert progress_event_call[0][0] == ResourceEventType.BATCH_LOADING_PROGRESS.value
            progress_event_args = progress_event_call[0][1]
            
            loaded_count_tracker += 1
            assert progress_event_args.batch_id == batch_id
            assert progress_event_args.resource_path == path
            assert progress_event_args.loaded_count == loaded_count_tracker
            assert progress_event_args.total_resources == len(asset_paths)

        # 3. 验证 CompleteEvent
        complete_event_call = mock_event_manager.emit.call_args_list[-1]
        assert complete_event_call[0][0] == ResourceEventType.BATCH_LOADING_COMPLETE.value
        complete_event_args = complete_event_call[0][1]

        assert complete_event_args.batch_id == batch_id
        assert complete_event_args.loaded_count == len(asset_paths) # 尝试加载的总数
        assert complete_event_args.total_resources == len(asset_paths)
        assert complete_event_args.succeeded is False
        assert len(complete_event_args.errors) == len(asset_paths)
        for i, path in enumerate(asset_paths):
            assert complete_event_args.errors[i][0] == path
            assert error_message_template.format(path=path) in complete_event_args.errors[i][1]

        # 验证 AssetManager.load_asset 被正确调用次数
        assert mock_load_asset_method.call_count == len(asset_paths)

    # def test_load_assets_batch_with_kwargs(self, asset_manager_instance, mock_event_manager):
    #     pass 