class PatchdiffError(Exception):
    code = 1

    def __init__(self, message: str, code: int | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if code is not None:
            self.code = code


class CliArgumentError(PatchdiffError):
    code = 10


class ConfigError(PatchdiffError):
    code = 10


class FileNotFoundErrorPatch(PatchdiffError):
    code = 20


class IngestError(PatchdiffError):
    code = 30


class DiffBackendError(PatchdiffError):
    code = 40


class DecompileError(PatchdiffError):
    code = 50


class LlmError(PatchdiffError):
    code = 60


class ValidationError(PatchdiffError):
    code = 70


class ReportError(PatchdiffError):
    code = 80
