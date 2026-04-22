from django.shortcuts import render


# Create your views here.
class IndexView:
    def __call__(self, request):
        return render(request, "index.html")


index_view = IndexView()
