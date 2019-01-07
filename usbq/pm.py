import pluggy
import importlib
import logging

from collections import ChainMap, OrderedDict

from .hookspec import USBQ_EP, USBQHookSpec, USBQPluginDef

__all__ = ['AVAILABLE_PLUGINS', 'enable_plugins']

log = logging.getLogger(__name__)

# Load the plugin manager and list available plugins
pm = pluggy.PluginManager(USBQ_EP)
pm.add_hookspecs(USBQHookSpec)
pm.load_setuptools_entrypoints(USBQ_EP)

AVAILABLE_PLUGINS = OrderedDict(ChainMap({}, *pm.hook.usbq_declare_plugins()))

# Add optional
HOOK_MOD = 'usbq_hooks'
HOOK_CLSNAME = 'USBQHooks'
AVAILABLE_PLUGINS['usbq_hooks'] = USBQPluginDef(
    name='usbq_hooks',
    desc='Optional user-provided hook implementations automatically loaded from from ./usbq_hooks.py',
    mod=HOOK_MOD,
    clsname=HOOK_CLSNAME,
    optional=True,
)


def enable_plugins(pm, pmlist, disabled=[]):
    for pdinfo in pmlist + [('usbq_hooks', {})]:
        pdname, pdopts = pdinfo

        if pdname not in AVAILABLE_PLUGINS:
            raise ValueError(f'{pdname} is not a valid USBQ plugin.')

        if pdname in disabled:
            log.info(f'Disabling plugin {pdname}.')
            continue

        pd = AVAILABLE_PLUGINS[pdname]

        try:
            mod = importlib.import_module(pd.mod)
            cls = getattr(mod, pd.clsname)
            log.debug(f'Loaded {pd.name} plugin from {pd.mod}:{pd.clsname}')
        except ModuleNotFoundError:
            if pd.optional:
                log.info(
                    f'Could not load optional plugin {pd.name}: Module not available.'
                )
            else:
                raise
        except AttributeError:
            if pd.optional:
                log.info(
                    f'Could not load optional plugin {pd.name}: Could not instantiate {pd.clsname}.'
                )
            else:
                raise

        pm.register(cls(**pdopts))
