from django.views.generic import FormView, View


class PeoplefinderView(View):
    pass


class HtmxFormView(FormView, PeoplefinderView):
    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
