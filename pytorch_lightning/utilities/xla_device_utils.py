from warnings import warn

warn(
    "`xla_device_utils` package has been renamed to `xla_device` since v1.2 and will be removed in v1.4",
    DeprecationWarning
)

XLA_AVAILABLE = importlib.util.find_spec("torch_xla") is not None
#: define waiting time got checking TPU available in sec
TPU_CHECK_TIMEOUT = 100

if XLA_AVAILABLE:
    import torch_xla.core.xla_model as xm


def inner_f(queue, func, *args, **kwargs):  # pragma: no cover
    try:
        queue.put(func(*args, **kwargs))
    except Exception:
        traceback.print_exc()
        queue.put(None)


def pl_multi_process(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        queue = Queue()
        proc = Process(target=inner_f, args=(queue, func, *args), kwargs=kwargs)
        proc.start()
        proc.join(TPU_CHECK_TIMEOUT)
        try:
            return queue.get_nowait()
        except q.Empty:
            traceback.print_exc()
            return False

    return wrapper


class XLADeviceUtils:
    """Used to detect the type of XLA device"""

    TPU_AVAILABLE = None

    @staticmethod
    def _fetch_xla_device_type(device: torch.device) -> str:
        """
        Returns XLA device type

        Args:
            device: (:class:`~torch.device`): Accepts a torch.device type with a XLA device format i.e xla:0

        Return:
            Returns a str of the device hardware type. i.e TPU
        """
        if XLA_AVAILABLE:
            return xm.xla_device_hw(device)

    @staticmethod
    def _is_device_tpu() -> bool:
        """
        Check if device is TPU

        Return:
            A boolean value indicating if the xla device is a TPU device or not
        """
        if XLA_AVAILABLE:
            device = xm.xla_device()
            device_type = XLADeviceUtils._fetch_xla_device_type(device)
            return device_type == "TPU"

    @staticmethod
    def xla_available() -> bool:
        """
        Check if XLA library is installed

        Return:
            A boolean value indicating if a XLA is installed
        """
        return XLA_AVAILABLE

    @staticmethod
    def tpu_device_exists() -> bool:
        """
        Runs XLA device check within a separate process

        Return:
            A boolean value indicating if a TPU device exists on the system
        """
        if XLADeviceUtils.TPU_AVAILABLE is None and XLA_AVAILABLE:
            XLADeviceUtils.TPU_AVAILABLE = pl_multi_process(XLADeviceUtils._is_device_tpu)()
        return XLADeviceUtils.TPU_AVAILABLE
