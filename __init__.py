"""MOSSの漫画用コマ割りデータセットとComfyUI画面拡張。"""
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = './web'
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

try:
    from server import PromptServer
except ModuleNotFoundError as error:
    if error.name != 'server':
        raise
else:
    from .picker_api import register_routes
    if getattr(PromptServer.instance, '_moss_panel_picker_registered', False):
        raise RuntimeError('MOSSコマ割りノードが重複しています。旧版のフォルダまたはジャンクションを外し、ComfyUIを再起動してください。')
    register_routes(PromptServer.instance.routes)
    PromptServer.instance._moss_panel_picker_registered = True
