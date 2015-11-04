from nodeconductor.core import NodeConductorExtension


class SugarCRMExtension(NodeConductorExtension):

    @staticmethod
    def django_app():
        return 'nodeconductor_sugarcrm'

    @staticmethod
    def rest_urls():
        from .urls import register_in
        return register_in
