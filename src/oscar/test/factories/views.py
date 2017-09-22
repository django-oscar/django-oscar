from django.views import generic


class BandCreateView(generic.CreateView):
    pass


class BandListView(generic.ListView):
    pass


class BandUpdateView(generic.UpdateView):
    pass


class BandDeleteView(generic.DeleteView):
    pass
