from security.throttling import UnsuccessfulLoginThrottlingValidator, SuccessfulLoginThrottlingValidator


validators = (
    UnsuccessfulLoginThrottlingValidator(60, 2),
    UnsuccessfulLoginThrottlingValidator(10 * 60, 10),
    SuccessfulLoginThrottlingValidator(60, 2),
    SuccessfulLoginThrottlingValidator(10 * 60, 10),
)
