import Breadcrumbs from './Breadcrumbs';

export default function PageHeader({ 
  title, 
  description, 
  breadcrumbs = [], 
  actions = null,
  className = ''
}) {
  return (
    <div className={`mb-6 ${className}`}>
      {breadcrumbs.length > 0 && (
        <div className="mb-4">
          <Breadcrumbs items={breadcrumbs} />
        </div>
      )}
      
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-sm text-gray-500">
              {description}
            </p>
          )}
        </div>
        
        {actions && (
          <div className="mt-4 flex md:ml-4 md:mt-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
} 