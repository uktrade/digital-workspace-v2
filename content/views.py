from django.views.generic.edit import FormView
from content.forms import NewsCategoryForm


class NewsCategoryFormView(FormView):
    form_class = NewsCategoryForm

    def get_success_url(self):
        if 'next' in self.request.GET:
            return self.request.GET.get('next')
        return reverse_lazy('index')

    # def form_valid(self, form):
    #     # This method is called when valid form data has been POSTed.
    #     # It should return an HttpResponse.
    #     form.send_email()
    #     return super().form_valid(form)
