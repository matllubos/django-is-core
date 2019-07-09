from is_core.auth.permissions import BasePermission


class RelatedCoreAllowed(BasePermission):
    """
    Grant permission if core permission with the name grants access
    """

    name = None

    def __init__(self, name=None):
        super().__init__()
        if name:
            self.name = name

    def has_permission(self, name, request, view, obj=None):
        return (
            view.related_core.permission.has_permission(self.name or name, request, view, obj)
            if view.related_core else True
        )
