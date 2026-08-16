def inventory_context(request):
    is_staff = False
    if request.user.is_authenticated:
        is_staff = (
            request.user.is_superuser or 
            request.user.is_staff or 
            request.user.groups.filter(name__in=['Inventory Managers', 'Stockers', 'Managers', 'Admin']).exists()
        )
    return {
        'is_inventory_staff': is_staff
    }
